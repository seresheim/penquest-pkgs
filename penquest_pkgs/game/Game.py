import asyncio
import itertools
import dataclasses

from typing import Optional, Dict, List, Any, Tuple, Union

from penquest_pkgs.network.game_messages import outbound as OutboundMessages
from penquest_pkgs.network.game_messages.outbound import dataclass_to_dict
from penquest_pkgs.utils.Handler import EventBasedObject
from penquest_pkgs.model import (
    GameState,
    ExternalGamePhase,
    InternalGamePhase,
    GameOptions,
    Lobby,
    Player, 
    Asset,
    Game,
    Actor
)

import penquest_pkgs.network.game_messages.message_models as Messages 

from penquest_pkgs.constants.Events import Events
from penquest_pkgs.constants.Commands import Commands
from penquest_pkgs.constants.MessageType import MessageType
from penquest_pkgs.constants.GameStoragePhase import GameStoragePhase
from penquest_pkgs.constants.GameInteractions import GameInteractionType
from penquest_pkgs.utils.logging import get_logger
from penquest_pkgs.game.mappers import map_message2model, map_model2message

        
GAME_PHASE_MAP = {
    "Starting": 0,
    "InitDraw": 1,
    "Shopping": 2,
    "Attack": 3,
    "Defense": 4,
    "Ended": 5
}

VALID_ATTACK_MASKS = ["C", "I", "A", "CI", "CA", "IA", "CIA"]


class Game(EventBasedObject):
    """The central class for interacting with the PenQuest server.

    The main interaction element of this class for tasks are its event listening
    capabilities inherited from EventBasedObject. The Game class communicates
    with the PenQuest server via GameInputInterpreter and GameOutputInterpreter.
    GameInputInterpreter listens for incoming messages from the server and calls
    the corresponding method of the internal class Input of Game. Thus the 
    game state updates. GameOutputInterpreter registers a listener for SEND
    events that are dispatched from the Game class itself and forwards all 
    messages received this way to the PenQuest server.  
    Note that many methods are executed by different tasks, one \"main\" task, 
    that is created by the environment and one task per incoming message.

    One central interaction element for the environment is the 
    interaction_buffer that signals the environment which type of interaction
    the game requires in the current state. This also includes interactions for
    game establishment. 

    Attributes:
        phase(GameStoragePhase): Indicates in which 'general' phase the game
            currently is. These can be Start, Lobby, Running and Ended and
            should not be confused with ExternalGamePhase, which indicate the current
            phase within a running game. Thus the ExternalGamePhases usually change
            while the GameStoragePhase has the value 'Running'.
        lobby(): the game lobby, required to create a new game
        actor_id(): ID of the role within a running game (e.g. ID of the role
            'Attacker1')
        actor_connection_id(): 
        game_state(GameState): state of the current game. This field is set, as
            soon as a new game was created
        action_detected_history(List): 
        input(Input): instance of the private class Input that contains the
            handling methods to process incoming messages
        output(Output): instance of the private class Output that contains the
            methods to send messages to the PenQuest server.
        offer_received_this_turn(bool): indicates whether the role has already
            received an offer of actions which to choose the next actions from
        interaction_buffer(asyncio.Queue): stores the next interactions the 
            game requires from the environment

    """

    def __init__(self):
        """Initializes all attributes"""
        super(Game, self).__init__()

        self.phase = GameStoragePhase.Start
        self.lobby: Lobby = None
        self.actor_connection_id: str = None

        self.game_state: GameState = None
        self.action_detected_history: List = []

        self.input = Game.Input(self)
        self.output = Game.Output(self)
        self.offer_received = False

        # Create interaction queue this indicates that player interaction is 
        # needed and which kind/type of interaction it is
        self.interaction_buffer = asyncio.Queue()
        self.interaction_buffer.put_nowait(
            GameInteractionType.CREATE_OR_JOIN_LOBBY
        )
        
    async def close(self):
        """Sends an END message to the message listenting task and puts an END
        interaction type into the interaction buffer
        """
        get_logger(__name__).info(
            f"closing game with connection_id '{self.actor_connection_id}'"
        )
        await self.dispatch_event(Events.SEND, [MessageType.COMMAND, None])
        self.interaction_buffer.put_nowait(GameInteractionType.END)

    # Event handling
    async def dispatch_command(
            self,
            command: str,
            msg_type: str,
            message: Any = None
        ):
        """Redirects commands to the GameOutputInterpreter by using the SEND 
        event

        :param command: name of the command that is dispatched
        :param msg_type: type of message that is sent. This is specific to the
            protocol between environment and gateway, but dependent on the 
            command.
        :param message: the message object that stores all information about the
            command
        :return: _description_
        """
        return await self.dispatch_event(
            Events.SEND, 
            [ 
                msg_type, 
                {
                    'event': command,
                    'data': dataclass_to_dict(message) if message is not None else {}
                }
            ]
        )


    class Input:
        """Contains all message handling routines for messages from the PenQuest
        server. This functionality is exctracted from the Game class to reduce 
        the API surface.

        Methods of this class are called by the GameInputInterpreter which
        interprets incoming messages from the PenQuest Server and then calls the
        corresponding handling method in this class. Mostly, their
        functionality is restricted to updating the current GameState object in
        the Game class and dispatching corresponding events.
        """

        def __init__(self, outer_class_object: 'Game'):
            """Initializes all attributes

            :param outer_class_object: references to the game object
            """
            self.game = outer_class_object

        async def _await_correct_game_storage_phase(
                self, 
                game_storage_phase: Union[GameStoragePhase, List[GameStoragePhase]]
            ):
            """Awaits until the current GameStoragePhase is one of the desired
            correct phases.

            :param game_storage_phase: either a correct phase or a list of
                correct phases
            :raises asyncio.TimeoutError: the phases did not change to a correct
                phase within provided the time window
            """
            try:
                correct_phases = []
                if isinstance(game_storage_phase, GameStoragePhase):
                    correct_phases = [game_storage_phase]
                else:
                    correct_phases = game_storage_phase
                
                while self.game.phase not in correct_phases:
                    await self.game.await_event(
                        Events.GAME_STORAGE_PHASE_CHANGED
                    )
            except asyncio.TimeoutError:
                raise asyncio.TimeoutError(
                    f"Wrong game storage phase! Current phase is "
                    f"{self.game.phase} but exepcetd one of "
                    f"{', '.join([x.value for x in correct_phases])}"
                )
            
        def _hide_asset(self, asset_id: int):
            """Hides an asset that is currently visible on the board

            :param asset_id: ID of asset to hide
            :raise RuntimeError: game state is None
            :raise RuntimeError: asset not found
            :raise RuntimeError: ID is not unique
            """
            if self.game.game_state is None:
                raise RuntimeError("Cannot start game if game state is not set")

            # Find asset on board and remove it
            list_index = [
                i for i in range(len(self.game.game_state.assets_on_board)) 
                if self.game.game_state.assets_on_board[i].id == asset_id
            ]
            if len(list_index) == 0: 
                raise RuntimeError(f"Found no asset with id {asset_id}")
            if len(list_index) > 1: 
                raise RuntimeError(f"Found more than one asset with the id {asset_id}")
            self.game.game_state.assets_on_board.pop(list_index[0])

        def _reveal_asset(self, asset: Asset):
            """Reveals an asset on the game board

            :param asset: Assets to include on the game board
            :raise RuntimeError: game state is None
            """
            if self.game.game_state is None:
                raise RuntimeError("Cannot start game if game state is not set")

            # Add to board if not already on board
            if asset in self.game.game_state.assets_on_board: return
            self.game.game_state.assets_on_board.append(asset)

        async def update_player(self, player: Messages.Player):
            """Updates the information stored about the player object that
            represents the agent in the game.

            :param player: player object that represents the agent
            :event players_changed: notifies all waiting tasks that a
                'players_changed' event occured
            """
            self.game.actor_connection_id = player.connection_id

            if self.game.lobby is not None:
                changed = False
                for slot, p in self.game.lobby.items():
                    if player.id == p.id and player.connection_id == p.connection_id:
                        self.game.lobby[slot] = map_message2model(player)
                        changed = True
                        break
                if changed:
                    await self.game.dispatch_event(
                        Events.PLAYERS_CHANGED,
                        { 'players': self.game.lobby.players }
                    )

        async def set_lobby_information(self, lobby: Messages.Lobby):
            """Sets the lobby information of the game

            :param lobby: Dict of lobby info
            :raises RuntimeError: game is not in the GameStoragePhase 'start' or
                'lobby', which are required to receive such a message
            :event lobby_changed: notifies all waiting tasks that a
                'lobby_changed' event occured
            :event game_storage_phase_changed: notifies all waiting tasks that 
                'game_storage_phase_changed' changed to 'lobby'
            """
            if self.game.phase not in [GameStoragePhase.Start, GameStoragePhase.Lobby]:
                raise RuntimeError(
                    "Cannot set lobby information when game is not in start or "
                    "lobby phase"
                )
            
            scenario_changed = False
            if self.game.lobby is not None and self.game.lobby.scenario != lobby.scenario:
                scenario_changed = True

            self.game.lobby = map_message2model(lobby)
            if self.game.phase != GameStoragePhase.Lobby:
                self.game.phase = GameStoragePhase.Lobby
            await self.game.dispatch_event(
                Events.LOBBY_CHANGED,
                {'lobby': self.game.lobby}
            )
            await self.game.dispatch_event(
                Events.GAME_STORAGE_PHASE_CHANGED,
                {'game_phase': self.game.phase}
            )

            if scenario_changed:
                await self.game.dispatch_event(
                    Events.SCENARIO_CHANGED,
                    {"scenario": lobby.scenario}
                )

        async def set_lobby_player_information_for_slot(
                self,
                player: Messages.Player,
                slot: int
            ):
            """Adds a player to a game lobby

            :param player: Player to add to the game
            :param slot: Slot to add the player to
            :raises RuntimeError: GameStoragePhase ist not 'lobby'
            :raises RuntimeError: Slot index is not in the correct range
            :raises RuntimeError: game lobby is currently None
            :event players_changed: notifies all waiting tasks that a
                'players_changed' event occured
            """
            if self.game.phase != GameStoragePhase.Lobby:
                raise RuntimeError(
                    "Cannot add player when game is not in lobby phase"
                )
            if not slot >= 1:
                raise RuntimeError("Slot index starts at 1")
            if self.game.lobby is None:
                raise RuntimeError(
                    "Cannot add player when game is not in lobby phase"
                )

            self.game.lobby.players[slot] = map_message2model(player)
            await self.game.dispatch_event(
                Events.PLAYERS_CHANGED,
                { 'players': self.game.lobby.players }
            )

        async def remove_player(self, player: Messages.Player, slot: int):
            """Removes a player from the game lobby

            :param player: Player to remove from the game
            :param slot: Slot to remove the player from
            :raises RuntimeError: Slots is not in the correct range
            :raises RuntimeError: game lobby is None
            """
            if not slot >= 1:
                raise RuntimeError("Slot index starts at 1")
            if self.game.lobby is None:
                raise RuntimeError(
                    "Cannot add player when game is not in lobby phase"
                )
            
            del self.game.lobby.players[slot]

        async def set_scenario(self, scenario: Messages.ScenarioTeaser):
            """Sets the scenario of the game

            :param scenario: the scenario object to set
            :raise RuntimeError: GameStorgePhase is not 'lobby'
            :event scenario_changed: notifies all waiting tasks that a
                'players_changed' event occured
            """
            if self.game.phase != GameStoragePhase.Lobby:
                raise RuntimeError("Cannot set scenario when not in lobby")

            self.game.lobby.scenario = map_message2model(scenario)
            await self.game.dispatch_event(
                Events.SCENARIO_CHANGED,
                { 'scenario': scenario }
            )

        async def changed_slots(
                self,
                connection_id: str,
                new_slot: int,
                old_slot: int
            ):
            """Changes the slot of a player in the current game lobby

            :param connection_id: ID of the player that is changed
            :param new_slot: the new slot the agent now has
            :param old_slot: the old slot the agent was before
            :raise RuntimeError: GameStoragePhase is not 'lobby'
            :event players_changed: notifies all waiting tasks that a
                'players_changed' event occured
            """
            if self.game.phase != GameStoragePhase.Lobby:
                raise RuntimeError("Cannot set scenario when not in lobby")
            
            self.game.lobby.players[new_slot] = self.game.lobby.players[old_slot]
            del self.game.lobby.players[old_slot]
            await self.game.dispatch_event(
                Events.PLAYERS_CHANGED,
                { 'players': self.game.lobby.players }
            )

        async def game_crashed(self, code: int, reason: str):
            """Logs a game crash message from the server and tries to end the
            game gracefully by leaving it first and then closing it.

            :param code: error code of the crash
            :param reason: error message of the crash
            """
            get_logger().error(f"The game crashed! Reason: f{code} - {reason}")
            await self.game.leave_game()
            await self.game.close()

        async def update_game_options(
                self,
                new_game_options: Messages.GameOptions
            ):
            """Updates local game options with the given game options

            :param new_game_options: GameOptions to update local game options 
                with
            :raise RuntimeError: GameStoragePhase is not 'lobby' or the current
                game lobby is None
            :event game_options_changed: notifies all waiting tasks that a
                'game_options_changed' event occured
            """
            if self.game.phase != GameStoragePhase.Lobby or self.game.lobby is None:
                raise RuntimeError(
                    "Cannot change game options when game is not in lobby phase"
                )

            self.game.lobby.game_options = map_message2model(new_game_options)
            await self.game.dispatch_event(
                Events.GAME_OPTIONS_CHANGED,
                { 'game_options': new_game_options }
            )

        async def lobby_left(self, player: Messages.Player):
            """Closes the game if the player that left the game was the agent
            itself.

            :param player: player that left the game (lobby)
            """
            get_logger().info(
                    f"Player {player.name}({player.id}) left the current "
                    "lobby/game"
                )
            if player.connection_id == self.game.actor_connection_id:
                await self.game.close()
                
        async def start_game(self, game: Optional[Messages.Game] = None):
            """Creates the initial GameState and sets the current 
            GameStoragePhase to 'running'

            :param game: the game object that started, defaults to None
            :raises RuntimeError: GameStoragePhase is not 'lobby'; games can
                only be created from this GameStoragePhase
            :raises RuntimeError: game lobby is None
            :raises RuntimeError: scenarios of lobby and game do not match
            :raises RuntimeError: connection_id is not set
            :raises RuntimeError: agent was not provided with a role
            :event game_storage_phase_changed: notifies all waiting tasks that a
                'game_storage_phase_changed' event occured
            :event game_started: notifies all waiting tasks that a
                'game_started' event occured
            """
            if self.game.phase != GameStoragePhase.Lobby:
                raise RuntimeError(
                    "Cannot start game when game is not in lobby phase"
                )
            if self.game.lobby is None:
                raise RuntimeError("Cannot start game if lobby is not set")
            if self.game.lobby.scenario is None or self.game.lobby.scenario.id != game.scenario_id:
                raise RuntimeError(
                    "Scenario of lobby is not the same as scenario of game"
                )
            if self.game.actor_connection_id is None:
                raise RuntimeError(
                    "Cannot start game when player id or connection id is not "
                    "set"
                )
            if self.game.actor_connection_id not in game.roles:
                raise RuntimeError("Didn't find role of this player in game")

            self.game.game_state = GameState(
                name = self.game.lobby.code,
                scenario = self.game.lobby.scenario,
                game_options = self.game.lobby.game_options,
                from_lobby = self.game.lobby,
                actor_connection_id = self.game.actor_connection_id,
                #actor_id = self.game.actor_id,
                shop = map_message2model(game.shop),
                selection_amount = game.amount_selection
            )

            self.game.phase = GameStoragePhase.Running
            await self.game.dispatch_event(
                Events.GAME_STORAGE_PHASE_CHANGED,
                {'game_storage_phase': self.game.phase}
            )

            await self.set_players_and_roles(game.players, game.roles)
            await self.game.dispatch_event(Events.GAME_STARTED)

        async def set_players_and_roles(
                self, 
                players: List[Messages.Player], 
                roles: Dict[str, Messages.Actor]
            ):
            """Sets the players and their roles; updates the assets in the game
            state; updates actions/equipment on the agents hand

            :param players: List - List of players
            :param roles: Dict - Dict of roles
            :raises RuntimeError: GameStoragePhase is not 'running'
            :raises RuntimeError: game state is None
            :raises RuntimeError: connection ID is None
            :raises RuntimeError: connection ID is not in game
            :raises RuntimeError: player role is not set
            :event board_changed: notifies all waiting tasks that a
                'board_changed' event occured
            :event hand_changed: notifies all waiting tasks that a
                'hand_changed' event occured
            :event equipment_changed: notifies all waiting tasks that a
                'equipment_changed' event occured
            :event player_role_changed: notifies all waiting tasks that a
                'player_role_changed' event occured
            """
            if self.game.phase != GameStoragePhase.Running:
                raise RuntimeError(
                    "Cannot set players when game is not running"
                )
            if self.game.game_state is None:
                raise RuntimeError("Cannot start game if game state is not set")
            if self.game.game_state.actor_connection_id is None:
                raise RuntimeError(
                    "Cannot start game when player id or connection id is not "
                    "set"
                )
            if self.game.game_state.actor_connection_id not in roles.keys():
                raise RuntimeError("Didn't find role of this player in game")
            
            role = roles.get(self.game.game_state.actor_connection_id, None)
            if role is None: raise RuntimeError("Player role is not set")

            # Set player roles
            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                roles=map_message2model(roles)
            )

            # Update game state with asset list from role
            role = self.game.get_player_role()
            for asset in role.visible_assets:
                if asset in self.game.game_state.assets_on_board: continue
                self.game.game_state.assets_on_board.append(asset)
            # Update game state with asset list from role if role is defender
            if role.type == "defender":
                for asset in role.assets:
                    if asset in self.game.game_state.assets_on_board: continue
                    self.game.game_state.assets_on_board.append(asset)

            await self.game.dispatch_event(
                Events.BOARD_CHANGED,
                { 'board': self.game.game_state.assets_on_board }
            )

            # Updates actions on the hand of the player
            for action in role.actions:
                self.game.game_state.hand.append(action)
            await self.game.dispatch_event(
                Events.HAND_CHANGED,
                { 'hand': self.game.game_state.hand }
            )

            # Updates equpment on the hand of the player
            for equipment in role.equipment:
                self.game.game_state.equipment.append(equipment)
            await self.game.dispatch_event(
                Events.EQUIPMENT_CHANGED,
                { 'equipment': self.game.game_state.equipment }
            )

            await self.game.dispatch_event(
                Events.PLAYER_ROLE_CHANGED,
                { 'role': role }
            )

        async def set_player_attribute(self, attribute: str, value: int):
            """Sets an attribute of the player

            :param attribute: str - Attribute to set
            :param value: int - Value to set the attribute to
            :raise RuntimeError: GameStoragePhase is not 'running'
            :raise RuntimeError: game state is None
            :raise RuntimeError: agents role is not set
            :raise ValueError: role does not have the provided attribute
            :event player_attribute_changed: notifies all waiting tasks that a
                'player_attribute_changed' event occured
            """
            if self.game.phase != GameStoragePhase.Running:
                raise RuntimeError(
                    "Cannot set player attribute when game is not running"
                )
            if self.game.game_state is None:
                raise RuntimeError(
                    "Cannot start game if game state is not set"
                )

            # Get role and check if attribute is in role
            role = self.game.get_player_role()
            if role is None: raise RuntimeError("Player role is not set")
            if not hasattr(role, attribute):
                raise ValueError(
                    f"Attribute '{attribute}' is not in player attributes"
                )
            
            # Set attribute and dispatch event
            setattr(role, attribute, value)
            await self.game.dispatch_event(
                Events.PLAYER_ATTRIBUTE_CHANGED,
                { 'attribute': attribute, 'value': value }
            )

        async def set_game_phase(self, game_phase: Union[str, int]):
            """Sets the current game phase

            :param game_phase: the game phase the current game phase should be 
                set to
            :raise RuntimeError: game state is None
            :raise ValueError: unkown game phase
            :event game_phase_changed: notifies all waiting tasks that a
                'game_phase_changed' event occured
            """
            await self._await_correct_game_storage_phase(
                [GameStoragePhase.Running, GameStoragePhase.Ended]
            )
            if self.game.game_state is None:
                raise RuntimeError("Cannot start game if game state is not set")

            # Convert game phase to ExternalGamePhase object if it is not already one
            if type(game_phase) == str:
                if game_phase not in GAME_PHASE_MAP:
                    raise ValueError(f"Unknown game phase: {game_phase}")
                game_phase = GAME_PHASE_MAP[game_phase]
            if type(game_phase) == int:
                game_phase = ExternalGamePhase(game_phase)
            
            is_my_turn = self.game._is_my_turn(game_phase)
            if is_my_turn:
                internal_phase = InternalGamePhase.Shopping
            else:
                internal_phase = InternalGamePhase.Idle

            # Set game phase and dispatch event
            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                external_phase=game_phase,
                internal_phase=internal_phase
            )
            await self.game.dispatch_event(
                Events.GAME_PHASE_CHANGED,
                { 'game_phase': game_phase }
            )

            # Decide on next interaction type
            interaction_type = None
            if game_phase == ExternalGamePhase.InitDraw:
                interaction_type = GameInteractionType.CHOOSE_ACTION
            elif is_my_turn:
                if self.game.game_state.turn == 1:
                    if internal_phase == InternalGamePhase.Shopping and self.game.lobby.game_options.equipment_shop_mode > 0:
                        interaction_type = GameInteractionType.SHOPPING_PHASE
                    else:
                        interaction_type = GameInteractionType.PLAY_CARD
                else:
                    # each turn starts with redrawing an action, only the first
                    # turn starts immediately with playing an action card
                    interaction_type = GameInteractionType.CHOOSE_ACTION

            # Put interaction type in buffer
            if interaction_type is not None:
                self.game.interaction_buffer.put_nowait(interaction_type)

        async def set_assortment(self, equipment: List[Messages.Equipment]):
            """Sets the assortment of the agent which it can shop from during
            the shopping phase

            :param equipment: List of equipment that can be shopped from during
                the shopping phase
            :raise RuntimeError: game state is None
            :raise RuntimeError: shop is None
            :event shop_changed: notifies all waiting tasks that a
                'shop_changed' event occured
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            if self.game.game_state is None:
                raise RuntimeError("Cannot set assortment if game state is not set")
            if self.game.game_state.shop is None:
                raise RuntimeError("Cannot set assortment if shop is not set")

            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                shop=map_message2model(equipment)
            )
            await self.game.dispatch_event(
                Events.SHOP_CHANGED,
                { 'shop': equipment }
            )

        async def add_equipment(self, equipment: List[Messages.Equipment]):
            """Adds equipment to the agent's equipment and removes it from the
            shop

            :param equipment: List of equipment the agent received
            :raise RuntimeError: game state is None
            :event equipment_changed: notifies all waiting tasks that a
                'equipment_changed' event occured
            :event shop_changed: notifies all waiting tasks that a
                'shop_changed' event occured
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            if self.game.game_state is None:
                raise RuntimeError(
                    "Cannot set equipment if game state is not set"
                )
            
            equipment = map_message2model(equipment)
            equipment_ids = []
            # Update equipment hand
            for eq in equipment:
                equipment_ids.append(eq.id)
                self.game.game_state.equipment.append(eq)
            await self.game.dispatch_event(
                Events.EQUIPMENT_CHANGED,
                {'equipment': equipment }
            )

            # Update shop for missing equipment that was purchased
            shop_list_indexes = [
                i for i, it in enumerate(self.game.game_state.shop) 
                if it.id in equipment_ids
            ]
            for i, rm_index in enumerate(shop_list_indexes):
                # '- i' is only used to account for the fact that the list is 
                # getting smaller 
                self.game.game_state.shop.pop(rm_index - i) 
            await self.game.dispatch_event(
                Events.SHOP_CHANGED, 
                { 'shop': self.game.game_state.shop }
            )

        async def add_new_actions_to_hand(
                self, 
                new_actions: List[Messages.Action]
            ):
            """Adds new actions to the hand of the player (like after drawing 
            cards)

            :param new_actions: List of new actions
            :raise RuntimeError: game state is None
            :event hand_changed: notifies all waiting tasks that a
                'hand_changed' event occured
            """
            # in case of defener at the game end the GamePhaseChanged event
            # might come before the new actions arrive, therefore adding the
            # GameStoragePhase.Ended such that the game does not wait
            # indefintely because it already formally ended.
            await self._await_correct_game_storage_phase(
                [GameStoragePhase.Running, GameStoragePhase.Ended]
            )
            if self.game.game_state is None:
                raise RuntimeError(
                    "Cannot add new actions to hand if game state is not set"
                )
            
            new_actions = map_message2model(new_actions)
            # Add new actions to hand
            self.game.game_state.hand.extend(new_actions)
            await self.game.dispatch_event(
                Events.HAND_CHANGED,
                { 'hand': self.game.game_state.hand }
            )
            if self.game._is_my_turn(self.game.game_state.external_phase):
                if self.game.lobby.game_options.equipment_shop_mode > 0:
                    self.game.interaction_buffer.put_nowait(
                        GameInteractionType.SHOPPING_PHASE
                    )
                else:
                    self.game.interaction_buffer.put_nowait(
                        GameInteractionType.PLAY_CARD
                    )

        async def set_all_actions_playable(
                self, 
                playable_results: List[Messages.Playable]
            ):
            """Sets the playable actions

            :param playable_results: List of playable actions
            :raise RuntimeError: game state is None
            :event all_actions_playable: notifies all waiting tasks that a
                'all_actions_playable' event occured
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            if self.game.game_state is None:
                raise RuntimeError(
                    "Cannot set playable actions if game state is not set"
                )
            
            # TODO: process incoming information

            await self.game.dispatch_event(
                Events.ALL_ACTIONS_PLAYABLE,
                { 'actions': playable_results }
            )

        async def played_action_reply(
                self, 
                successful: bool, 
                action: Messages.Action
            ):
            """Feedback from the gameserver if the played action was successful

            :param successful: bool - Whether the action was successful
            :param action: Dict - The action that was played
            :raise RuntimeError: game state is None
            :event play_action_reply: notifies all waiting tasks that a
                'play_action_reply' event occured
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            if self.game.game_state is None:
                raise RuntimeError(
                    "Cannot play action reply if game state is not set"
                )

            await self.game.dispatch_event(
                Events.PLAY_ACTION_REPLY, 
                { 
                    'successful': successful,
                    'action': action 
                }
            )

        async def add_actions_detected_event(
                self, 
                actions: List[Messages.Action]
            ):
            """Adds an actions detected event

            :param actions: List of actions that were detected
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            actions = map_message2model(actions)
            self.game.action_detected_history.append(actions)

        async def update_assets(self, asset_changes: Messages.AssetChanges):
            """Updates the assets on the board with new incoming information, in
            terms of newly revealed or hidden assets

            :param change: Changes to the board
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )

            for asset in asset_changes.revealed:
                self._reveal_asset(map_message2model(asset))
            for asset_id in asset_changes.hidden:
                self._hide_asset(asset_id)

        async def remove_cards(
                self,
                actionIds: List[int],
                equipmentIds: List[int]
            ):
            """removes cards (actions or equipment) from the agents hand

            :param actionIds: List of action IDs that should be removed
            :param equipmentIds: List of equipment IDs that should be removed
            """
            actions_to_be_removed = [
                action 
                for action in self.game.game_state.hand 
                if action.id in actionIds
            ]
            equipment_to_be_removed = [
                equipment 
                for equipment in self.game.game_state.equipment 
                if equipment.id in equipmentIds
            ]
            for action in actions_to_be_removed:
                self.game.game_state.hand.remove(action)
            for equipment in equipment_to_be_removed:
                self.game.game_state.equipment.remove(equipment)

        async def game_turn_changed(self, currentTurn: int):
            """Sets game state to the new turn and initializes turn variables

            :param currentTurn: number of turn the game is currently in
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )

            self.game.game_state = dataclasses.replace(self.game.game_state, turn=currentTurn)
            self.game.offer_received = False

        async def update_asset(self, asset: Messages.Asset):
            """Updates the information of a single asset

            :param asset: Asset to be changed
            """
            await self._await_correct_game_storage_phase(
                [GameStoragePhase.Running, GameStoragePhase.Ended]
            )

            if any([asset.id == a.id for a in self.game.game_state.assets_on_board]):
                self._hide_asset(asset.id)
                self._reveal_asset(map_message2model(asset))

        async def set_received_offering(
                self, 
                actions: List[Messages.Action], 
                amount_selection: int
            ):
            """Sets the received offer the agent can choose from when redrawing
            an action card

            :param actions: List of actions the offer consists of
            :param amount_selection: amount of actions the agent needs to choose
                from the offer
            :raise RuntiemError: game state is None
            :event selection_offer_changed: notifies all waiting tasks that a
                'selection_offer_changed' event occured
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            if self.game.game_state is None:
                raise RuntimeError(
                    "Cannot receive offer if game state is not set"
                )
            
            # Set offer in game state
            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                selection_amount=amount_selection, 
                selection_choices=map_message2model(actions)
            )
            self.game.offer_received = True

            # Dispatch event
            await self.game.dispatch_event(
                Events.SELECTION_OFFER_CHANGED, 
                { 
                    'actions': actions, 
                    'amount_selection': amount_selection
                }
            )

        async def game_ended(
                self,
                endState: Messages.GameEndedState,
                endMessage: str,
                postGameSummary: Messages.PostGameSummary = None,
                turn:int = None
            ):
            """Updates the game state accordingly for the ended game, sets
            correct game (storage) phase and notifies listeners

            :param game_end_state: the state the game ended in (won,lost,etc)
            :param finished_message: Message to display to the players
            :param turn: Turn the game ended on
            :raise RuntimeError: game state is None
            :event game_storage_phase_changed: notifies all waiting tasks that a
                'game_storage_phase_changed' event occured
            :event game_ended: notifies all waiting tasks that a
                'game_ended' event occured
            """
            if self.game.game_state is None:
                raise RuntimeError("Cannot start game if game state is not set")

            self.game.phase = GameStoragePhase.Ended
            await self.game.dispatch_event(
                Events.GAME_STORAGE_PHASE_CHANGED,
                { 'game_storage_phase': self.game.phase }
            )
            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                end_state = map_message2model(endState)
            )

            # TODO: Log game end and results
            await self.game.dispatch_event(
                Events.GAME_ENDED, 
                {
                    'role': self.game.get_player_role(),
                    'result': endState,
                    'finished_messages': endMessage,
                    'turn': turn if turn is not None else self.game.game_state.turn
                }
            )
            self.game.interaction_buffer.put_nowait(GameInteractionType.END)

        async def error(
                self, 
                error_id:Union[int, List[int]], 
                error_message: Union[str, List[str]],
                multiple_errors: bool
            ):
            """Error handling when a server error appears (logs the error) and
            tries to end the game gracefully

            :param error_id: ID of the error that appeared
            :param error_message: message of the error that appeared
            :param multiple_errors: Indicates whether multiple errors appeared
            """
            if not isinstance(error_id, list):
                error_id = [error_id]
                error_message = [error_message]
            for eid, emsg in zip(error_id, error_message):
                get_logger(__name__).error(f"Error {eid}: {emsg}")
            if self.game.phase.value > GameStoragePhase.Start.value:
                await self.game.output.leave_game()
                await self.game.close()

        async def got_kicked(self):
            """Closes the game"""
            self.game.close()

        async def game_player_changed(
            self, 
            new_connection_id: str, 
            new_player_id: int, 
            old_connection_id: str, 
            old_player_id: int, 
            player: Player
        ):
            """Updates information about a player

            :param new_connection_id: new connection ID of the player
            :param new_player_id: new ID of the player
            :param old_connection_id: old connection ID of the player
            :param old_player_id: old ID of the player
            :param player: player object that holds more detailed information
            """
            if self.game.actor_connection_id == old_connection_id:
                self.game.actor_connection_id = new_connection_id
            
            
            idx = None
            # if a player with the old connection ID already exists, remove it
            # and store the position it was stored
            for i, p in enumerate(self.game.game_state.players):
                if p.connection_id == old_connection_id:
                    self.game.game_state.players.pop(i)
                    idx = i
                    break

            # if no player is found, add the player at the last position
            if idx is None:
                idx = len(self.game.game_state.players)
            self.game.game_state.players.insert(idx, player)

        async def update_game_state(self, game: Messages.Game):
            """Update the current game state via a full game state update from
            the PenQuest server

            :param game: full state of the current game
            :raises RuntimeError: connection ID is None
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            if self.game.actor_connection_id not in game.roles:
                raise RuntimeError("Didn't find role of this player in game")


            self_actor = map_message2model(game.roles[self.game.actor_connection_id])
            self.game.game_state = GameState(
                actor_connection_id = self.game.actor_connection_id,
                turn=game.turn,
                shop = map_message2model(game.shop),
                selection_amount = game.amount_selection,
                phase=game.phase,
                players=map_message2model(game.players),
                roles=map_message2model(game.roles),
                hand=self_actor.actions,
                equipment=self_actor.equipment,
                assets_on_board=self_actor.visible_assets+self_actor.assets,
                selection_choices=map_message2model(game.actions_offered)
            )
    
        async def game_left(self):
            """Forwards the event and to end the game gracefully
            
            :event game_left: notifies all listeners that a 'game_left' event 
                was received """
            await self.game.dispatch_event(Events.GAME_LEFT)

    class Output:
        """Contains all commands sent by the client to the PenQuest server.
        This functionality is exctracted from the Game class to reduce the API 
        surface.

        Methods of this class are usually called by methods of the Game class
        and is a lower level API, that kicks off the outgoing messages to the
        server.
        """

        def __init__(self, outer_class_object: 'Game'):
            """Initializes all attributes"""
            self.game = outer_class_object
        
        async def request_connection_id(self):
            """Sends a message of type 'connect' to the gateway in order to
            receive a connection_id
            """
            await self.game.dispatch_command(
                "",
                MessageType.CONNECT,
                {}
            )
            
        async def join_lobby(self, code: str):
            """Sends a 'join_lobby' message

            :param code: code of the lobby to join to
            """
            await self.game.dispatch_command(
                Commands.JOIN_LOBBY, 
                MessageType.JOIN, 
                OutboundMessages.JoinLobbyMessage(code)
            )

        async def create_new_game_lobby(self):
            """Sends a create_new_game_lobby message"""
            await self.game.dispatch_command(
                Commands.CREATE_NEW_GAME_LOBBY, 
                MessageType.SETUP
            )

        async def set_seed(self, seed: int):
            """Sends a seed to the server for the RNG

            :param seed: seed for the RNG
            """
            await self.game.dispatch_command(
                Commands.SET_SEED, 
                MessageType.COMMAND, 
                OutboundMessages.SetSeedMessage(seed)
            )

        async def set_goal(self, goald_id: str):
            """Sends a set_goal message

            :param goal_id: ID of the goal that should be set
            """
            await self.game.dispatch_command(
                Commands.SELECT_GOAL, 
                MessageType.COMMAND, 
                OutboundMessages.SetGoalMessage(goald_id)
            )

        async def select_scenario(self, scenario_id: str):
            """Sends a create_new_game_lobby message

            :param scenario_id: ID of the scenario that should be selected
            """
            await self.game.dispatch_command(
                Commands.SELECT_SCENARIO, 
                MessageType.COMMAND, 
                OutboundMessages.SelectScenarioMessage(scenario_id)
            )

        async def update_game_options(self, options: GameOptions):
            """sends an update_game_options command

            :param options: new game options
            """
            await self.game.dispatch_command(
                Commands.UPDATE_GAME_OPTIONS, 
                MessageType.COMMAND, 
                OutboundMessages.UpdateGameOptionsMessage(
                    map_model2message(options)
                )
            )

        async def add_bot(self, slot: int, bot_type: int = 0):
            """Sends an add_bot message

            :param slot: slot on which the bot should be added in the lobby
            :param bot_type: type of bot that should be added, defaults to 0
            """
            await self.game.dispatch_command(
                Commands.ADD_BOT, 
                MessageType.COMMAND, 
                OutboundMessages.AddBotMessage(slot, bot_type)
            )

        async def set_player_readiness(self, ready: bool):
            """Sends a set_player_ready message

            :param ready: ready status of the agent
            """
            await self.game.dispatch_command(
                Commands.SET_PLAYER_READINESS, 
                MessageType.COMMAND, 
                OutboundMessages.SetPlayerReadinessMessage(ready)
            )

        async def change_slot(self, new_slot: int):
            """Changes the slot of the agent within the lobby

            Args:
                new_slot (int): the slot the agent wants to change to
            """
            await self.game.dispatch_command(
                Commands.CHANGE_SLOT, 
                MessageType.COMMAND, 
                OutboundMessages.ChangeSlotMessage(new_slot)
            )

        async def get_valid_actions(self, actions: List[Tuple[int,int,int]]):
            """Sends a get_valid_actions message to see which actions can be
            played in the current game state

            :param actions: all actions under consideration
            """
            action_dicts = []

            for action in actions:
                action_dict = {
                    "action_id": self.game.game_state.hand[action[0]].id,
                    "support_action_ids": [],
                    "equipment_ids": [],
                }
                if action[1] is not None and action[1] > 0:
                    action_dict["support_action_ids"].append(
                        self.game.game_state.hand[action[1]-1].id
                    )
                if action[2] is not None and action[2] > 0:
                    action_dict["equipment_ids"].append(
                        self.game.game_state.equipment[action[2]-1].id
                    )
                action_dicts.append(action_dict)
            
            await self.game.dispatch_command(
                Commands.GET_VALID_ACTIONS, 
                MessageType.COMMAND, 
                OutboundMessages.GetValidActionsMessage(action_dicts)
            )

        async def select_actions(self, action_ids: List[int]):
            """Sends a select_actions message"""
            await self.game.dispatch_command(
                Commands.SELECT_ACTIONS, 
                MessageType.COMMAND, 
                OutboundMessages.SelectActionsMessage(action_ids)
            )

        async def play_action(
                self, 
                action_id: int, 
                target_asset_id: int, 
                attack_mask: str, 
                support_action_ids: List[int] = None, 
                equipment_ids: List[int] = None, 
                response_target_id: int = 0
            ):
            """Sends a play_action message

            :param action_id: ID of the action that should be played
            :param target_asset_id: ID of the asset the action should be played
            :param attack_mask: attack mask that is used to play the action
            :param support_action_ids: IDs of support actions that are played 
                along the main action, defaults to None
            :param equipment_ids: ID of equipment that is played along the main
                action, defaults to None
            :param response_target_id: ID of a main action of an opponen the
                current main action should remedy against, defaults to 0
            :raises ValueError: invalid attack mask
            """
            if attack_mask not in VALID_ATTACK_MASKS:
                raise ValueError(
                    f"attack_mask must be one of the following: "
                    f"{VALID_ATTACK_MASKS}"
                )
            
            await self.game.dispatch_command(
                Commands.PLAY_ACTION, 
                MessageType.COMMAND, 
                OutboundMessages.PlayActionMessage(
                    action_id,
                    target_asset_id,
                    attack_mask,
                    support_action_ids if support_action_ids else [],
                    equipment_ids if equipment_ids else [],
                    response_target_id
                )
            )

        async def buy_equipment(self, equipment_ids: List[int]):
            """Sends a buy_equipment message

            :param equipment_ids: List of equipment IDs that should be bought
            """
            await self.game.dispatch_command(
                Commands.BUY_EQUIPMENT, 
                MessageType.COMMAND, 
                OutboundMessages.BuyEquipmentMessage(
                    equipment_ids, 
                    endShopping=True
                )
            )
        
        async def shopping_finished(self):
            """Sends a shopping_finished message"""
            await self.game.dispatch_command(
                Commands.SHOPPING_FINISHED, 
                MessageType.COMMAND
            )

        async def surrender(self):
            """Sends a surrender message"""
            await self.game.dispatch_command(
                Commands.SURRENDER, 
                MessageType.COMMAND,
                {}
            )

        async def leave_game(self):
            """Sends a leave_game message"""
            await self.game.dispatch_command(
                Commands.LEAVE_GAME,
                MessageType.COMMAND
            )


    async def request_connection_id(self):
        """Requests a connection_id from the gateway and awaits until
        the ID was received
        """
        if self.actor_connection_id is not None:
            raise Exception("Already received a connection id")
        
        await self.output.request_connection_id()
        get_logger(__name__).debug("Request for a connection id was sent")
        await self.await_event(Events.CONNECTION_ID_RECEIVED)

    async def join_game(self, game_id: str):
        """Joins an already existing lobby with the given id

        :param game_id: Id of the game lobby to join to
        """
        if self.phase != GameStoragePhase.Start:
            raise Exception("Cannot join game when game is not in start phase")

        await self.output.join_lobby(game_id)

        # Ask for lobby changes and player readiness
        self.interaction_buffer.put_nowait(GameInteractionType.CHANGE_LOBBY_PROPERTIES)
        self.interaction_buffer.put_nowait(GameInteractionType.PLAYER_READY)

    async def create_new_lobby(
            self, 
            scenario_id: Optional[int] = None, 
            options: Optional[Dict[str, int]] = None
        ):
        """Creates a lobby with the given lobby info

        :param scenario_id: Id of the scenario to select
        :param options: Options to set for the game
        :return: Lobby object
        :event game_storage_phase_changed: notifies all waiting tasks that a
            'game_storage_phase_changed' event occured
        """
        if self.phase != GameStoragePhase.Start:
            raise Exception("Cannot create lobby when game is not in start phase")
        
        await self.output.create_new_game_lobby()
        ret = await self.await_event(Events.LOBBY_CHANGED)

        if scenario_id is not None:
            await self.output.select_scenario(scenario_id)
            await self.await_event(Events.SCENARIO_CHANGED)
        if options is not None:
            game_options = GameOptions.from_dict(options)
            await self.output.update_game_options(game_options)
            await self.await_event(Events.GAME_OPTIONS_CHANGED)
        
        self.phase = GameStoragePhase.Lobby
        await self.dispatch_event(
            Events.GAME_STORAGE_PHASE_CHANGED,
            {'game_storage_phase': self.phase}
        )

        # Ask for lobby changes and player readiness
        self.interaction_buffer.put_nowait(
            GameInteractionType.CHANGE_LOBBY_PROPERTIES
        )
        self.interaction_buffer.put_nowait(GameInteractionType.PLAYER_READY)

        return ret
    
    async def set_seed(self, seed: int):
        """Sets the seed of the game

        :param seed: seed for the RNG
        """
        if self.phase != GameStoragePhase.Lobby:
            raise RuntimeError("Cannot set seed when game is not in lobby phase")
        if self.lobby is None:
            raise RuntimeError("Cannot set seed when lobby is not set")

        await self.output.set_seed(seed)

    async def set_goal(self, goal_idx: int):
        """Sets the goal of the game

        :param goal_idx: index of the goal to set
        """
        if self.phase != GameStoragePhase.Lobby:
            raise RuntimeError("Cannot set goal when game is not in lobby phase")
        if self.lobby is None:
            raise RuntimeError("Cannot set goal when lobby is not set")
        if goal_idx-1 >= len(self.lobby.availableGoals):
            raise ValueError("Goal index out of bounds")
        
        goal = self.lobby.availableGoals[goal_idx-1]

        await self.output.set_goal(goal.id)

    async def add_bot(self, bot_type: int = 0):
        """Adds a bot to the lobby

        :param bot_type: Type of bot to add to the lobby 
            (0 = Random Bot, 1 = Not So Random Bot), defaults to 0
        """
        if self.phase != GameStoragePhase.Lobby:
            raise RuntimeError("Cannot add bot when game is not in lobby phase")
        if self.lobby is None:
            raise RuntimeError("Cannot add bot when lobby is not set")

        slot = 1
        while slot in self.lobby.players:
            slot += 1
        await self.output.add_bot(slot, bot_type=bot_type)

    async def wait_for_players(self, amount: int, timeout_in_sec: int = 240):
        """Waits until there are at least the given amount of players in the 
        lobby

        :param amount: Amount of players to wait for
        :param timeout_in_sec: Timeout in seconds
        """
        if self.phase != GameStoragePhase.Lobby:
            raise RuntimeError(
                "Cannot wait for players when game is not in lobby phase"
            )
        if self.lobby is None:
            raise RuntimeError("Cannot wait for players when lobby is not set")
        
        if amount <= 0: return
        while len(self.lobby.players) -1 < amount:
            await self.await_event(
                Events.PLAYERS_CHANGED, 
                timeout=timeout_in_sec
            )

    async def set_player_readiness(self, ready: bool = True):
        """Creates a lobby with the given lobby info

        :param ready: bool indicating if player is ready
        """
        if self.phase != GameStoragePhase.Lobby:
            raise RuntimeError(
                "Cannot change players readiness when game is not in lobby"
            )
        if self.lobby is None:
            raise RuntimeError(
                "Cannot change players readiness when lobby is not set"
            )
        if len(self.lobby.players) < 2:
            raise RuntimeError(
                "Cannot change players readiness when there are not at least 2 "
                "players in the lobby"
            )

        await self.output.set_player_readiness(ready)
    
    async def change_slot(self, new_slot: int):
        """Changes slot of the agent in the game lobby

        :param new_slot: identifier of the new slot the agent wants to move
        :raises RuntimeError: GameStoragePhase is not 'lobby'
        """
        if self.phase != GameStoragePhase.Lobby:
            raise RuntimeError("Cannot change slot when game is not in lobby")
        
        await self.output.change_slot(new_slot)
        await self.await_event(Events.PLAYERS_CHANGED)
        
    async def get_curr_phase(self) -> ExternalGamePhase:
        """Returns the current phase of the game

        :return: Current phase of the game
        """
        if self.game_state is None:
            return ExternalGamePhase.Starting
        return self.game_state.external_phase

    def _is_my_turn(self, current_phase: ExternalGamePhase) -> bool:
        """Returns whether it is the current player's turn

        :param current_phase: Current phase of the game
        :return: Whether it is the current player's turn
        :raise RuntimeError: GameStoragePhase is not running or ended
        :raise RuntimeError: game state is None
        """
        if self.phase not in [ GameStoragePhase.Running, GameStoragePhase.Ended ]:
            raise RuntimeError(
                "Cannot advance game phase when game is not running"
            )
        if self.game_state is None:
            raise RuntimeError("Cannot start game if game state is not set")

        role = self.get_player_role()
        if role is None: return False

        if current_phase not in [ExternalGamePhase.Attacker, ExternalGamePhase.Defender]:
            return False
        
        is_attacker = role.type == 'attacker' and current_phase == ExternalGamePhase.Attacker
        is_defender = role.type == 'defender' and current_phase == ExternalGamePhase.Defender

        return is_attacker or is_defender

    def get_player_role(
            self,
            connection_id: Optional[str] = None
        ) -> Actor:
        """Returns the role of the agent's player (None) or with the given 
        connection id

        :param connection_id: Connection id of the player to get the role of
        :return: Role of the player or None if no role was found
        """
        if self.game_state is None or self.game_state.roles is None:
            return None

        return self.game_state.roles.get(
            connection_id or self.game_state.actor_connection_id,
            None
        )
    
    def set_player_role(self, role: Dict, connection_id: Optional[str] = None):
        """Sets the role of the agent's player (None) or with the given
        connection id

        :param role: Role to set
        :param connection_id: Connection id of the player to get the role of
        """
        if self.game_state is None or self.game_state.roles is None:
            return None
        
        id = connection_id or self.game_state.actor_connection_id
        if id not in self.game_state.roles: return None

        self.game_state.roles[id] = role

    async def next_interaction_type(
            self,
            timeout_in_sec: int = 240
        ) -> GameInteractionType:
        """Returns the next interaction type when interaction is needed

        :param timeout_in_sec: int - Timeout in seconds
        :return: GameInteractionType - Interaction type
        """
        interaction_type = await asyncio.wait_for(
            self.interaction_buffer.get(), 
            timeout_in_sec
        )
        if interaction_type == GameInteractionType.CHOOSE_ACTION and not self.offer_received:
            await self.await_event(Events.SELECTION_OFFER_CHANGED)

        return interaction_type

    async def buy_equipment(self, equipment_ids: List[int]):
        """Buy's equipment of the provided euqipment IDs list

        :param equipment_ids: IDs of the equipment to buy
        :raises RuntimeError: GameStoragePhase is not 'running'
        :raises RuntimeError: game state is None
        :raises RuntimeError: GamePhase is not 'shopping'
        """
        if self.phase != GameStoragePhase.Running:
            raise RuntimeError("Cannot shop when game is not running")
        if self.game_state is None:
            raise RuntimeError("Cannot start game if game state is not set")
        if self.game_state.internal_phase != InternalGamePhase.Shopping:
            raise RuntimeError("Cannot shop outside the shopping phase")
        if len(equipment_ids) == 0: return # Nothing to buy

        await self.output.buy_equipment(equipment_ids)

        self.game_state = dataclasses.replace(
            self.game_state, 
            internal_phase=InternalGamePhase.Playing
        )
        self.interaction_buffer.put_nowait(GameInteractionType.PLAY_CARD)

    async def remove_equipment_from_shop(self, equipmentIds: List[str]):
        """Removes equipment from the shop

        :param eq_ids: List of equipment IDs to remove
        """
        if self.game_state is None:
            raise RuntimeError("Cannot remove equipment if game state is not set")
        if self.game_state.shop is None:
            raise RuntimeError("Cannot remove equipment if shop is not set")

        for eq_id in equipmentIds:
            for eq in self.game_state.shop:
                if eq.id == eq_id:
                    self.game_state.shop.remove(eq)
                    break

    async def finish_shopping(self):
        """Finishs the shopping phase for the agent

        :raises RuntimeError: GameStoragePhase is not 'running'
        :raises RuntimeError: game state is None
        :raises RuntimeError: GamePhase is not 'shopping'
        """
        if self.phase != GameStoragePhase.Running:
            raise RuntimeError("Cannot shop when game is not running")
        if self.game_state is None:
            raise RuntimeError("Cannot start game if game state is not set")
        if self.game_state.internal_phase != InternalGamePhase.Shopping:
            raise RuntimeError("Cannot shop outside the shopping phase")

        await self.output.shopping_finished()

        self.game_state = dataclasses.replace(
            self.game_state, 
            internal_phase=InternalGamePhase.Playing
        )
        self.interaction_buffer.put_nowait(GameInteractionType.PLAY_CARD)

    async def get_valid_actions(self) -> List[Tuple[int,int,int,int,int,int]]:
        """Returns a list of all valid actions currently available to the player

        :raises RuntimeError: GameStoragePhase is not 'running'
        :raises RuntimeError: game state is None
        :raises RuntimeError: incorrect GamePhase
        :raises RuntimeError: no playable actions
        :return: list of all valid actions
        """

        if self.phase != GameStoragePhase.Running:
            raise RuntimeError(
                "Cannot get valid actions when game is not running"
                )
        if self.game_state is None:
            raise RuntimeError(
                "Cannot get valid actions if game state is not set"
            )
        if self._is_my_turn(self.game_state.external_phase) is False:
            raise RuntimeError(
                "Cannot get valid actions when it is not your turn"
            )

        all_action_combinations = self._get_all_action_combinatinations()
        
        # Send to gameserver to get only valid actions and await reply
        await self.output.get_valid_actions(all_action_combinations)
        response = await self.await_event(Events.ALL_ACTIONS_PLAYABLE)
        playable_results = response.get('actions', {})

        comb_generators = []
        for i,result in playable_results.items():
            if not result.playable:
                continue
            action_combination = all_action_combinations[i]
            action = self.game_state.hand[action_combination[0]]
            if action.target_type == "single":
                target_asset_ids = result.possible_targets
            else:
                target_asset_ids = [0]
            if result.possible_response_target_ids is not None and len(result.possible_response_target_ids) > 0:
                response_target_ids = result.possible_response_target_ids 
            else:
                response_target_ids = { i: [0] for i in target_asset_ids}
            if action.requires_attack_mask:
                attack_masks = [1,2,3] # indices of ATTACK_MASKS
            else:
                attack_masks = [0] # index in ATTACK_MASKS

            for target_asset_id in target_asset_ids:
                asset_response_target_ids = response_target_ids[target_asset_id]
                if asset_response_target_ids is None or len(asset_response_target_ids) == 0:
                    asset_response_target_ids = [0]

                comb_generators.append(
                    itertools.chain.from_iterable(
                        [
                            itertools.product(
                                [action_combination[0]], 
                                [target_asset_id], 
                                attack_masks, 
                                [action_combination[1]], 
                                [action_combination[2]], 
                                asset_response_target_ids
                            )
                        ]
                    )
                )

        playable_actions = tuple(itertools.chain.from_iterable(comb_generators))

        if len(playable_actions) == 0:
            get_logger(__name__).error("No playable action available")
            await self.output.surrender()
            await self.output.leave_game()
        
        return playable_actions
    
    def _get_all_action_combinatinations(self) -> List[Tuple[int,int, int]]:
        """Returns all combinations of main actions, support actions, and 
        equipment

        :return: list of indices combinations
        """
        # Exclude permanent equipments from validation
        #TODO flag if its an permanent equipment 
        perm_eq = [
            "AttackTool",
            "SecuritySystem",
            "GlobalSingleUseDefenseEquipment",  # Types for covering edge cases
            "GlobalSingleUseAttackEquipment",   # Types for covering edge cases
        ]

        main_action_idxs = [
            index
            for index, action in enumerate(self.game_state.hand)
            if action.card_type == "main"
        ]
        support_action_idxs = [
            index +1
            for index, action in enumerate(self.game_state.hand)
            if action.card_type == "support"
        ]
        support_action_idxs.append(0)
        equipment_idxs = [
            idx +1
            for idx, data in enumerate(self.game_state.equipment)
            if data.type not in perm_eq
        ]
        equipment_idxs.append(0)
        
        return list(
            itertools.product(
                main_action_idxs, 
                support_action_idxs, 
                equipment_idxs
            ) 
        )

    async def play_action(
        self, 
        action_id: int, 
        target_asset_id: int, 
        attack_mask: str, 
        support_action_ids: List[int] = None, 
        equipment_ids: List[int] = None, 
        response_target_id: int = 0
    ) -> bool:
        """Plays an action this contains an card (main action), target asset, 
        attack mask, optional support actions and equipment

        :param action_id: Id of the action to play
        :param target_asset_id: Id of the target asset
        :param attack_mask: Mode of attack that the action aims at. 
            Possible Values: "C", "I", "A", "CI", "CA", "CIA"
        :param support_action_ids: List of support action ids
        :param equipment_ids: List of equipment ids
        :param response_target_id: Id of a previously played ID on the 
            target, the current main_action shall counter. Defaults to 0.
        """
        if support_action_ids is None:
            support_action_ids = []
        if equipment_ids is None:
            equipment_ids = []

        await self.output.play_action(
            action_id, 
            target_asset_id, 
            attack_mask, 
            support_action_ids, 
            equipment_ids, 
            response_target_id
        )
        action = await self.await_event(Events.PLAY_ACTION_REPLY)
        ret = action.get('successful', False)

        # no need to remove played actions here, PenQuest server sends a
        # separate message for that

        # TODO Debugging why?
        if isinstance(ret, list):
            if len(ret) == 0:
                # multi-targeted action didn't find any target 
                ret = False 
            else:
                ret = ret[0]
        return ret, action
    
    def has_to_select(self) -> bool:
        """Returns whether the agent has to select an action

        :raises RuntimeError: GameStoragePhase is not 'running'
        :raises RuntimeError: game state is None
        :return: indicates whether the agent has to select an action
        """
        if self.phase != GameStoragePhase.Running:
            raise RuntimeError("Cannot select when game is not running")
        if self.game_state is None:
            raise RuntimeError("Cannot start game if game state is not set")
        
        return self.game_state.selection_amount > 0 and len(self.game_state.selection_choices) > 0

    def get_selection(self) -> Tuple[int, List]:
        """returns the amount and a list of possible actions the agent can
        choose from

        :raises RuntimeError: GameStoragePhase is not 'running'
        :raises RuntimeError: game state is None
        :raises RuntimeError: agent doesn't have to select anything
        :return: amount and possible choices of the selection
        """
        if self.phase != GameStoragePhase.Running:
            raise RuntimeError("Cannot select when game is not running")
        if self.game_state is None:
            raise RuntimeError("Cannot start game if game state is not set")
        if not self.has_to_select():
            raise RuntimeError(
                "Cannot get selection when player doesn't have to select"
            )
        
        return (self.game_state.selection_amount, self.game_state.selection_choices)
    
    async def selection_choose(self, action_ids: List):
        """the agents selection is forwarded to the PenQuest server

        :param action_ids: List of selected action IDs 
        :raises RuntimeError: GameStoragePhase is not 'running'
        :raises RuntimeError: game state is None
        :raises RuntimeError: agent doesn't have to select anything
        """
        if self.phase != GameStoragePhase.Running:
            raise RuntimeError("Cannot select actions when game is not running")
        if self.game_state is None:
            raise RuntimeError("Cannot select actions if game state is not set")
        if not self.has_to_select():
            raise RuntimeError(
                "Cannot select when player doesn't have to select"
            )

        # Make selection and reset game state selection
        await self.output.select_actions(action_ids)
        self.game_state = dataclasses.replace(
            self.game_state, 
            selection_amount=0, 
            selection_choices=[]
        )

        # Turn counter increases by one
        self.game_state = dataclasses.replace(
            self.game_state, 
            turn=self.game_state.turn + 1
        )

    async def do_nothing(*args, **kwargs):
        """Does literally nothing"""
        pass

    async def set_connection_id(self, connectionId:str):
        """Sets the connection ID of the environment

        :param connectionId: the new connection ID to be set
        """
        get_logger(__name__).debug(
            f"updated connection_id to: '{connectionId}'"
        )
        self.actor_connection_id = connectionId
        if self.game_state is not None:
            self.game_state = dataclasses.replace(
                self.game_state, 
                actor_connection_id=connectionId
            )
        await self.dispatch_event(Events.CONNECTION_ID_RECEIVED)

    async def leave_game(self):
        """Leaves the current game and awaits until the PenQuest server confirms
        that the player left the game

        :raises RuntimeError: game state is None (no game to leave)
        """
        if self.lobby is None and self.game_state is None:
            raise RuntimeError("Nothing to leave")
        await self.output.leave_game()
        await self.await_event(Events.GAME_LEFT)
        
    def is_over(self) -> bool:
        """Indicates whether the current game is over or not

        :return: game over flag
        """
        return self.phase == GameStoragePhase.Ended
    