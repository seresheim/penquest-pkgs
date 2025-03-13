import asyncio
import dataclasses
import functools
import random
import time
from typing import Optional, Dict, List, Any, Tuple, Union

import pandas as pd
from penquest_pkgs.network.game_messages import outbound as OutboundMessages
from penquest_pkgs.network.game_messages.outbound import dataclass_to_dict
from penquest_pkgs.utils.Handler import EventBasedObject
from penquest_pkgs.model import (
    GameStateModel,
    GameOptionsModel,
    LobbyModel,
    PlayerModel,
    AssetModel,
    GameModel,
    ActorModel,
    ScenarioTeaserModel,
    EquipmentModel,
    ActionModel,
    AssetChangesModel,
    PostGameSummaryModel,
)
from penquest_pkgs.exceptions import Errors, PenQuestException
from penquest_pkgs.constants import (
    VALID_ATTACK_MASKS,
    Events,
    Commands,
    MessageType,
    GameStoragePhase,
    GameInteractionType,
    EquipmentShopMode,
    GamePhase,
    GameInteractionPhase,
    ActorType,
)
import penquest_pkgs.network.game_messages.message_models as Messages
from penquest_pkgs.utils.logging import get_logger
from penquest_pkgs.game.game_interactions import GameInteraction
from penquest_pkgs.game.GameInputInterpreter import GameInputInterpreter
from penquest_pkgs.game.GameOutputInterpreter import GameOutputInterpreter 
from penquest_pkgs.game.game_helper import GameHelper
from penquest_pkgs.game.actor_helper import ActorHelper

GAME_PHASE_MAP = {
    "Starting": 0,
    "DefenderPreSetup": 1,
    "InitDraw": 2,
    "Attack": 3,
    "Defense": 4,
    "Ended": 5
}


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
            should not be confused with GamePhase, which indicate the current
            phase within a running game. Thus the GamePhases usually change
            while the GameStoragePhase has the value 'Running'.
        lobby(): the game lobby, required to create a new game
        actor_id(): ID of the role within a running game (e.g. ID of the role
            'Attacker1')
        connection_id(): 
        game_state(GameState): state of the current game. This field is set, as
            soon as a new game was created
        action_detected_history(List): 
        input(Input): instance of the private class Input that contains the
            handling methods to process incoming messages
        output(Output): instance of the private class Output that contains the
            methods to send messages to the PenQuest server.
        offer_received_this_turn(bool): indicates whether the role has already
            received an offer of actions which to choose the next actions from
        shop_updated(bool): indicates whether the shop has been updated this 
            turn already.        
        interaction_buffer(asyncio.Queue): stores the next interactions the 
            game requires from the environment

    """

    def __init__(self, code: str = None, slot: int = None):
        """Initializes all attributes"""
        super(Game, self).__init__()

        self.code = code
        self.slot = slot
        self.phase = GameStoragePhase.Start
        self.lobby: LobbyModel = None
        self._connection_id: str = None

        self.game_state: GameStateModel = None
        self.action_detected_history: List = []

        self.input = Game.Input(self)
        self.output = Game.Output(self)
        self.offer_received = False
        self.shop_updated = False

        self._all_action_combinations: List[Tuple[int, int, int]] = None

        self.play_action_finished = asyncio.Event()

        # Create interaction queue this indicates that player interaction is
        # needed and which kind/type of interaction it is
        self.interaction_buffer = asyncio.Queue()
        
        self.rng = random.Random()
        self.leave_game_sent = False

        self.input_queue: asyncio.Queue = None
        self.input_task: asyncio.Task = None
        self.input_interpreter: GameInputInterpreter = None

        self.output_queue: asyncio.Queue = None
        self.output_task: asyncio.Task = None
        self.output_interpreter: GameOutputInterpreter = None

        self.logger = get_logger(__name__)

    @property  
    def connection_id(self) -> str:
        return self._connection_id
    
    @connection_id.setter
    def connection_id(self, connection_id: str):
        self._connection_id = connection_id
        if self.game_state is not None:
            role = self.game_state.role.type
        else:
            role = 'None'
        self.logger = get_logger(__name__, connection_id, self.code, role)

    async def start_listening(
            self, 
            input_channel: Union[asyncio.StreamWriter, asyncio.Queue], 
            output_channel: Union[asyncio.StreamWriter, asyncio.Queue]
        ):
        """Starts the listening tasks for incoming and outgoing messages and
        puts the first interaction into the interaction buffer
        """
        self.input_channel = input_channel
        self.output_channel = output_channel

        # Start listening output
        self.output_interpreter = GameOutputInterpreter(output_channel)
        self.output_task = asyncio.create_task(
            self.output_interpreter.start_listening(self)
        )
        current_name = self.output_task.get_name().split("-")
        self.output_task.set_name(
            f"Task-{current_name[-1]}(game_output)"
        )

        # Start listening input
        established_event = asyncio.Event()
        self.input_interpreter = GameInputInterpreter(input_channel)
        self.input_task = asyncio.create_task(
            self.input_interpreter.listen_to_messages(established_event, self)
        )
        current_name = self.input_task.get_name().split("-")
        self.input_task.set_name(
            f"Task-{current_name[-1]}(game_input)"
        )

        await established_event.wait()

        # Put first interaciton into buffer
        self.interaction_buffer.put_nowait(
            GameInteractionType.CREATE_OR_JOIN_LOBBY
        )

        
    async def close(self):
        """Cancels the listening tasks for input and output and puts an END
        interaction type into the interaction buffer
        """
        self.logger.info(
            f"closing game with connection_id '{self.connection_id}'"
        )
        self.interaction_buffer.put_nowait(GameInteractionType.END)
        
        try:
            self.input_task.cancel()
            self.output_task.cancel()
        except asyncio.CancelledError:
            # Silently exit tasks
            pass
        
        # destroy references for garbage collection
        self.input_interpreter.game = None
        self.output_interpreter.game = None

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
            ( 
                self.connection_id,
                msg_type, 
                {
                    'event': command,
                    'data': dataclass_to_dict(message) if message is not None else {}
                }
            )
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
            self.connection_id = None

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
            except asyncio.TimeoutError as e:
                raise asyncio.TimeoutError(
                    f"Wrong game storage phase! Current phase is "
                    f"{self.game.phase} but exepcetd one of "
                    f"{', '.join([str(x) for x in correct_phases])}"
                ) from e
          
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
            self.game.logger.debug(
                f"Removed asset with id {asset_id} from assets_on_board"
            )
            self._remove_assets_from_playable_combs([asset_id])

        def _reveal_asset(self, asset: AssetModel):
            """Reveals an asset on the game board

            :param asset: Assets to include on the game board
            :raise RuntimeError: game state is None
            """
            if self.game.game_state is None:
                raise RuntimeError("Cannot start game if game state is not set")

            # Add to board if not already on board
            if asset in self.game.game_state.assets_on_board: 
                return
            self.game.game_state.assets_on_board.append(asset)
            self.game.logger.debug(
                f"Added asset {asset.name}({asset.id}) to assets_on_board"
            )

        async def update_player(self, player: PlayerModel):
            """Updates the information stored about the player object that
            represents the agent in the game.

            :param player: player object that represents the agent
            :event players_changed: notifies all waiting tasks that a
                'players_changed' event occured
            """
            self.connection_id = player.connection_id

            if self.game.lobby is not None:
                changed = False
                for slot, p in self.game.lobby.players.items():
                    if player.id == p.id and player.connection_id == p.connection_id:
                        self.game.lobby.players[slot] = player
                        changed = True
                        break
                if changed:
                    await self.game.dispatch_event(
                        Events.PLAYERS_CHANGED,
                        { 'players': self.game.lobby.players }
                    )
            
            if self.game.game_state is not None:
                self.game.game_state = dataclasses.replace(
                    self.game.game_state, 
                    connection_id=self.connection_id
                )

        async def set_lobby_information(self, lobby: LobbyModel):
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

            self.game.lobby = lobby
            if self.game.phase != GameStoragePhase.Lobby:
                self.game.phase = GameStoragePhase.Lobby
            self.game.rng.seed(lobby.seed)
            self.game.logger.debug(f"Set seed: {lobby.seed}")

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
                player: PlayerModel,
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

            self.game.lobby.players[slot] = player
            await self.game.dispatch_event(
                Events.PLAYERS_CHANGED,
                { 'players': self.game.lobby.players }
            )

        async def remove_player(self, player: PlayerModel, slot: int):
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

        async def set_scenario(self, scenario: ScenarioTeaserModel):
            """Sets the scenario of the game

            :param scenario: the scenario object to set
            :raise RuntimeError: GameStorgePhase is not 'lobby'
            :event scenario_changed: notifies all waiting tasks that a
                'players_changed' event occured
            """
            if self.game.phase != GameStoragePhase.Lobby:
                raise RuntimeError("Cannot set scenario when not in lobby")

            self.game.lobby.scenario = scenario
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
            self.game.logger.error(
                f"The game crashed! Reason: f{code} - {reason}"
            )
            await self.game.leave_game()
            await self.game.close()

        async def update_game_options(
                self,
                new_game_options: GameOptionsModel
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

            self.game.lobby.game_options = new_game_options
            await self.game.dispatch_event(
                Events.GAME_OPTIONS_CHANGED,
                { 'game_options': new_game_options }
            )

        async def lobby_left(self, player: PlayerModel):
            """Closes the game if the player that left the game was the agent
            itself.

            :param player: player that left the game (lobby)
            """
            self.game.logger.info(
                    f"Player {player.name}({player.id}) left the current "
                    "lobby/game"
                )
            if player.connection_id == self.game.connection_id:
                await self.game.close()

        async def start_game(self, game: Optional[GameModel] = None):
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
            if self.game.connection_id is None:
                raise RuntimeError(
                    "Cannot start game when player id or connection id is not "
                    "set"
                )
            if self.game.connection_id not in game.roles:
                raise RuntimeError("Didn't find role of this player in game")

            self.game.game_state = GameStateModel(
                name = self.game.lobby.code,
                scenario = self.game.lobby.scenario,
                game_options = self.game.lobby.game_options,
                from_lobby = self.game.lobby,
                connection_id = self.game.connection_id,
                #actor_id = self.game.actor_id,
                shop = game.shop,
                selection_amount = game.amount_selection if game.amount_selection > 0 else -1,
            )

            self.game.phase = GameStoragePhase.Running
            await self.game.dispatch_event(
                Events.GAME_STORAGE_PHASE_CHANGED,
                {'game_storage_phase': self.game.phase}
            )

            await self.set_players_and_roles(game.players, game.roles)
            self.game.logger = get_logger(
                __name__, 
                self.game.connection_id, 
                self.game.code, 
                self.game.game_state.role.type
            )
            await self.game.dispatch_event(Events.GAME_STARTED)

        async def set_players_and_roles(
                self,
                players: List[PlayerModel], 
                roles: Dict[str, ActorModel]
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
            if self.game.game_state.connection_id is None:
                raise RuntimeError(
                    "Cannot start game when player id or connection id is not "
                    "set"
                )
            if self.game.game_state.connection_id not in roles.keys():
                raise RuntimeError("Didn't find role of this player in game")
            
            role = roles.get(self.game.game_state.connection_id, None)
            if role is None: 
                raise RuntimeError("Player role is not set")

            # Set player roles
            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                roles=roles
            )

            # Update game state with asset list from role
            role = self.game.get_player_role()
            for asset in role.visible_assets:
                if asset in self.game.game_state.assets_on_board: continue
                self.game.game_state.assets_on_board.append(asset)
            # Update game state with asset list from role if role is defender
            if role.type == ActorType.DEFENCE:
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
            # TODO: fix this workaround
            if attribute == "insightShield":
                attribute = "insight_shield"
            if not hasattr(role, attribute):
                raise ValueError(
                    f"Attribute '{attribute}' is not in player attributes"
                )
            
            # Set attribute and dispatch event
            setattr(role, attribute, value)
            self.game.logger.debug(
                f"player {role.name}({role.type}): changed {attribute} to {value}"
            )
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

            # Convert game phase to GamePhase object if it is not already one
            if type(game_phase) == str:
                if game_phase not in GAME_PHASE_MAP:
                    raise ValueError(f"Unknown game phase: {game_phase}")
                game_phase = GAME_PHASE_MAP[game_phase]

            # Set game phase
            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                game_phase=game_phase,
            )
            self.game.logger.debug(f"Game phase changed to {game_phase}")

            # get correct interaction phase
            is_my_turn = self.game._is_my_turn(game_phase)
            if is_my_turn:
                if self.game.game_state.turn > 1 or self.game.game_state.game_phase in [GamePhase.DefenderPreSetup, GamePhase.InitDraw]:
                    if not self.game.offer_received:
                        # wait until the selection offer has been received
                        await self.game.await_event(
                            Events.SELECTION_OFFER_CHANGED
                        )
                self.game.game_state = GameInteraction.move_from_idle(
                    self.game.game_state
                )
            else:
                self.game.game_state = GameInteraction.move_from_playing(
                    self.game.game_state
                )

            # dispatch event to whoever needs it
            if game_phase == GamePhase.Ended:
                self.game.phase = GameStoragePhase.Ended
            await self.game.dispatch_event(
                Events.GAME_PHASE_CHANGED,
                { 'game_phase': game_phase }
            )

            # Decide on next interaction type
            interaction_type = GameInteraction.get_interaction(
                self.game.game_state
            )
            if interaction_type  == GameInteractionType.PLAY_CARD:
                await self.game._switch_to_play_card_git()
            elif interaction_type == GameInteractionType.CHOOSE_ACTION:
                await self.game._switch_to_redraw_git()
            elif interaction_type is not None:
                self.game.interaction_buffer.put_nowait(interaction_type)
            elif interaction_type is None:
                self.game.logger.debug(
                    f"Idle waiting for game to proceed into a different phase."
                )
            else:
                raise ValueError(f"Unknown interaction type {interaction_type}")

        async def actor_detected(self, actorId: int):
            """Sets the game state discovered to True if the actor id matches

            :param actor_id: ID of the agent
            :raise RuntimeError: game state is None
            :event actor_detected: notifies all waiting tasks that a
                'actor_detected' event occured
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            if self.game.game_state is None:
                raise RuntimeError("Cannot set actor if game state is not set")

            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                discovered=True,
            )

        async def set_assortment(self, equipment: List[EquipmentModel]):
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
                shop=equipment
            )
            self.game.shop_updated = True
            await self.game.dispatch_event(
                Events.SHOP_UPDATED,
                { 'shop': equipment }
            )
            await self.game.dispatch_event(
                Events.SHOP_CHANGED,
                { 'shop': equipment }
            )

        async def add_equipment(self, equipment: List[EquipmentModel]):
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
            
            equipment = equipment
            equipment_ids = []
            # Update equipment hand
            for eq in equipment:
                equipment_ids.append(eq.id)
                self.game.game_state.equipment.append(eq)

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
            await self.game.dispatch_event(
                Events.EQUIPMENT_CHANGED,
                {'equipment': equipment }
            )

        async def remove_equipment_from_shop(self, equipmentIds: List[str]):
            """Removes equipment from the shop

            :param eq_ids: List of equipment IDs to remove
            """
            if self.game.game_state is None:
                raise RuntimeError("Cannot remove equipment if game state is not set")
            if self.game.game_state.shop is None:
                raise RuntimeError("Cannot remove equipment if shop is not set")

            for eq_id in equipmentIds:
                for eq in self.game.game_state.shop:
                    if eq.id == eq_id:
                        self.game.game_state.shop.remove(eq)
                        break
            await self.game.dispatch_event(
                Events.REMOVED_EQUIPMENT_FROM_SHOP,
                { 'equipment_ids': equipmentIds }
            )

        async def add_new_actions_to_hand(
                self,
                actions: List[ActionModel]
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
            
            # Add new actions to hand
            self.game.game_state.hand.extend(actions)

            action_str = ", ".join(
                [str(action.template_id) for action in actions]
            )
            self.game.logger.debug(f"Added actions {action_str} to hand")

            await self.game.dispatch_event(
                Events.HAND_CHANGED,
                { 'hand': self.game.game_state.hand }
            )
            await self.game.dispatch_event(
                Events.ACTIONS_RECEIVED,
                { 'actions': actions }
            )

        async def played_action_reply(
                self, 
                successful: bool, 
                action: ActionModel
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
                actions: List[ActionModel]
            ):
            """Adds an actions detected event

            :param actions: List of actions that were detected
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            self.game.action_detected_history.append(actions)

        async def update_assets(self, asset_changes: AssetChangesModel):
            """Updates the assets on the board with new incoming information, in
            terms of newly revealed or hidden assets

            :param change: Changes to the board
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )

            for asset in asset_changes.revealed:
                self._reveal_asset(asset)
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
            action_idxs = [
                self.game.game_state.hand.index(a) 
                for a in actions_to_be_removed
            ]
            eq_idxs = [
                self.game.game_state.equipment.index(e)+1 
                for e in equipment_to_be_removed
            ]

            # also remove validated_actions in case multiple actions are played
            # in one turn
            self._remove_actions_from_validated_actions(actions_to_be_removed)

            # remove playable actions in case multiple actions are played in one
            # turn
            if len(actions_to_be_removed) > 0:
                self._remove_actions_from_playable_combs(action_idxs)
            if len(equipment_to_be_removed) > 0:
                self._remove_equipment_from_playable_combs(eq_idxs)

            for action in actions_to_be_removed:
                self.game.game_state.hand.remove(action)
            for equipment in equipment_to_be_removed:
                self.game.game_state.equipment.remove(equipment)

        def _remove_actions_from_validated_actions(self, actions: List[ActionModel]):
            if self.game.game_state.validated_actions is None:
                return
            # first find validated actions object that is to be removed
            validated_actions = []
            for action in actions:
                for validated_action in self.game.game_state.validated_actions:
                    if validated_action.action == action:
                        validated_actions.append(validated_action)
                        break
            for validated_action in validated_actions:
                self.game.game_state.validated_actions.remove(validated_action)

        def _remove_actions_from_playable_combs(self, action_idxs: List[int]):
            """Removes actions from the playable actions combinations based
            on a list of action indices from the hand

            :param action_idxs: List of action indices in the order of the hand
            """
            # reduce the indices of all playable actions that come after the
            # actions that are removed by one.
            df = self.game.game_state.playable_actions
            if df is None or df.empty or df.size == 0:
                return
            
            for action_idx in action_idxs:
                # remove playable actions if action was main action
                df = df[df[0] != action_idx]
                df.loc[:, 0] = df[0].apply(lambda x: x - 1 if x > action_idx else x)

                # remove playable actions if action was support action
                df = df[df[3] != action_idx]
                df.loc[:, 3] = df[3].apply(lambda x: x - 1 if x > action_idx else x)

            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                playable_actions=df
            )

        def _remove_assets_from_playable_combs(self, asset_ids: List[int]):
            """Removes assets from the playable actions combinations based
            on a list of asset IDs

            :param asset_ids: List of asset IDs
            """
            df = self.game.game_state.playable_actions
            if df is None or df.empty or df.size == 0:
                return
            
            for asset_id in asset_ids:
                # remove playable actions if action was main action
                df = df[df[1] != asset_id]
                df.loc[:, 1] = df[1].apply(lambda x: x - 1 if x > asset_id else x)

            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                playable_actions=df
            )
        
        def _remove_equipment_from_playable_combs(self, eq_idxs: List[int]):
            """Removes assets from the playable actions combinations based
            on a list of asset IDs

            :param eq_idxs: List of equipment indices in the order of the hand
            """
            df = self.game.game_state.playable_actions
            if df is None or df.empty or df.size == 0:
                return
            
            for eq_idx in eq_idxs:
                # remove playable actions if action was main action
                df = df[df[4] != eq_idx]
                df.loc[:, 0] = df[4].apply(lambda x: x - 1 if x > eq_idx else x)

            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                playable_actions=df
            )

        async def game_turn_changed(self, currentTurn: int):
            """Sets game state to the new turn and initializes turn variables

            :param currentTurn: number of turn the game is currently in
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )

            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                turn=currentTurn
            )
            self.game.offer_received = False

        async def update_asset(self, asset: AssetModel):
            """Updates the information of a single asset

            :param asset: Asset to be changed
            """
            await self._await_correct_game_storage_phase(
                [GameStoragePhase.Running, GameStoragePhase.Ended]
            )

            if any([asset.id == a.id for a in self.game.game_state.assets_on_board]):
                self._hide_asset(asset.id)
                self._reveal_asset(asset)

        async def set_received_offering(
                self, 
                actions: List[ActionModel], 
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
                selection_choices=actions
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

        async def action_points_changed(self, actionPoints: int):
            """Sets the action points of the agent

            :param actionPoints: amount of action points the agent has
            :raise RuntimeError: game state is None
            :event action_points_changed: notifies all waiting tasks that a
                'action_points_changed' event occured
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            if self.game.game_state is None:
                raise RuntimeError(
                    "Cannot set action points if game state is not set"
                )

            # trap the second call in this if and let it await until the
            # play_action function is finished
            if self.game.play_action_finished.is_set():
                self.game.play_action_finished.clear()
                await self.game.play_action_finished.wait()

            self.game.game_state = dataclasses.replace(
                self.game.game_state, 
                action_points=actionPoints
            )

            # set event let second call run into the if condition above
            self.game.play_action_finished.set()
            self.game.logger.debug(f"Action points changed to {actionPoints}")

        async def game_ended(
                self,
                end_state: Messages.GameEndedState,
                end_message: str,
                post_game_summary: PostGameSummaryModel = None,
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
                game_phase=GamePhase.Ended,
                end_state = end_state
            )
            self.game.logger.info(
                f"Game ended in turn {self.game.game_state.turn}: {end_state} - "
                f"{end_message}"
            )
            # TODO: Log game end and results
            await self.game.dispatch_event(
                Events.GAME_ENDED,
                {
                    'role': self.game.get_player_role(),
                    'result': end_state,
                    'finished_messages': end_message,
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
                match eid:
                    case Errors.InvalidGamePhase:
                        # suppress error message if the game has ended
                        # if the other player for example leaves the game then
                        # the game ended message might come in between an action
                        # and then a GamePhaseMismatch error is thrown, because
                        # the game is already in the ended phase
                        if self.game.phase != GameStoragePhase.Ended and \
                            self.game.game_state.game_phase != GamePhase.Ended:
                            self.game.logger.error(f"Error {eid}: {emsg}")
                    case Errors.ActionNotPlayable:
                        # Another task is waiting for the play_action_reply
                        # event, so we need to send a reply in order to prevent 
                        # an error
                        
                        await self.game.dispatch_event(
                            Events.PLAY_ACTION_REPLY,
                            {
                                'successful': False,
                                'action': None
                            }
                        )
                    case Errors.NotEnoughCreditsError:
                        if self.game.game_state.interaction_phase != GameInteractionPhase.Shopping:
                            await self.game.dispatch_event(
                                Events.PLAY_ACTION_REPLY, 
                                { 
                                    'successful': False,
                                    'action': None
                                }
                            )
                    case Errors.NoPlayableActionError:
                        # Another task is waiting for the all_actions_playable
                        # event, so we need to send an empty list of playable
                        # actions in order to prevent an error
                        await self.game.dispatch_event(
                            Events.ALL_ACTIONS_PLAYABLE, 
                            { 
                                'playable_actions': []
                            }
                        )
                    case _:
                        self.game.logger.error(f"Error {eid}: {emsg}")
                        if self.game.phase.value > GameStoragePhase.Start.value:
                            await self.game.leave_game()
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
            player: PlayerModel
        ):
            """Updates information about a player

            :param new_connection_id: new connection ID of the player
            :param new_player_id: new ID of the player
            :param old_connection_id: old connection ID of the player
            :param old_player_id: old ID of the player
            :param player: player object that holds more detailed information
            """
            if self.game.connection_id == old_connection_id:
                self.game.connection_id = new_connection_id
                if self.game.game_state is not None:
                    self.game.game_state = dataclasses.replace(
                        self.game.game_state, 
                        connection_id=new_connection_id
                    )
            
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

        async def update_game_state(self, game: GameModel):
            """Update the current game state via a full game state update from
            the PenQuest server

            :param game: full state of the current game
            :raises RuntimeError: connection ID is None
            """
            await self._await_correct_game_storage_phase(
                GameStoragePhase.Running
            )
            if self.game.connection_id not in game.roles:
                raise RuntimeError("Didn't find role of this player in game")


            self_actor = game.roles[self.game.connection_id]
            self.game.game_state = GameStateModel(
                connection_id = self.game.connection_id,
                turn=game.turn,
                shop = game.shop,
                selection_amount = game.amount_selection,
                game_phase=game.phase,
                players=game.players,
                roles=game.roles,
                hand=self_actor.actions,
                equipment=self_actor.equipment,
                assets_on_board=self_actor.visible_assets+self_actor.assets,
                selection_choices=game.actions_offered
            )
            self.game.logger.info("Game state updated")
    
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
            
        async def join_lobby(self, code: str, slot: int = None):
            """Sends a 'join_lobby' message

            :param code: code of the lobby to join to
            """
            await self.game.dispatch_command(
                Commands.JOIN_LOBBY,
                MessageType.JOIN,
                OutboundMessages.JoinLobbyMessage(code, slot=slot)
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

        async def update_game_options(self, options: GameOptionsModel):
            """sends an update_game_options command

            :param options: new game options
            """
            await self.game.dispatch_command(
                Commands.UPDATE_GAME_OPTIONS, 
                MessageType.COMMAND, 
                OutboundMessages.UpdateGameOptionsMessage(options)
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

        async def select_actions(self, action_ids: List[int]):
            """Sends a select_actions message"""
            await self.game.dispatch_command(
                Commands.SELECT_ACTIONS, 
                MessageType.COMMAND, 
                OutboundMessages.SelectActionsMessage(
                    [Messages.SelectedActionMessageModel(aid, 1) for aid in  action_ids]
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
                    support_action_ids if support_action_ids is not None else [],
                    equipment_ids if equipment_ids is not None else [],
                    response_target_id
                )
            )

        async def finish_turn(self):
            """Sends a finish_turn message"""
            await self.game.dispatch_command(
                Commands.GAME_TURN_FINISHED, 
                MessageType.COMMAND
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

        async def surrender(self):
            """Sends a surrender message"""
            # set the phase of the game to ended. Waiting for the reply of
            # the server might take to long and the game might proceed with
            # the next action in the meantime.
            self.game.phase = GameStoragePhase.Ended
            self.game.game_state = dataclasses.replace(
                self.game.game_state,
                game_phase=GamePhase.Ended,
            )
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

        async def send_preset_done(self):
            """Sends a 'preset_done' message"""
            await self.game.dispatch_command(
                Commands.PRESET_DONE,
                MessageType.COMMAND
            )

    async def _switch_to_play_card_git(self):
        """Switches to the 'play card' game interaction type
        
        Before the game interaction type 'play card' can be published,
        the game state needs to be updated for valid actions.
        """
        validated_actions = GameHelper.get_validated_play_actions(self.game_state)
        self.game_state = dataclasses.replace(
            self.game_state,
            validated_actions=validated_actions
        )
        playable_actions = GameHelper.get_valid_actions(self.game_state)
        # set the dataframe for all playable actions
        df_playable_actions = pd.DataFrame(playable_actions)
        self.game_state = dataclasses.replace(
            self.game_state,
            playable_actions=df_playable_actions
        )
        await self.dispatch_event(
            Events.ALL_ACTIONS_PLAYABLE,
            { 'playable_actions': playable_actions}
        )
        if len(playable_actions) == 0:
            if self.game_state.actions_played_this_turn == 0:
                await self._handle_no_playable_action()
        # check if the current game state is still valid. There could be no
        # valid actions anymore, however until the server sends a reply we
        # already put the interaction type in the buffer if we don't check here
        # again.
        if self.game_state.game_phase != GamePhase.Ended:
            self.interaction_buffer.put_nowait(
                GameInteractionType.PLAY_CARD
            )

    async def _switch_to_redraw_git(self):
        """Switches to the 'redraw' game interaction type

        Before the game interaction type 'redraw' can be published, the game
        state needs to be updated for valid actions.
        """
        validated_actions = GameHelper.get_validated_redraw_actions(self.game_state)
        self.game_state = dataclasses.replace(
            self.game_state,
            validated_actions=validated_actions
        )
        if len(validated_actions) == 0:
            raise PenQuestException(
                Errors.NoPlayableActionError,
                "There is no playable action to redraw"
            )
        if self.game_state.game_phase != GamePhase.Ended:
            self.interaction_buffer.put_nowait(
                GameInteractionType.CHOOSE_ACTION
            )

    async def request_connection_id(self):
        """Requests a connection_id from the gateway and awaits until
        the ID was received
        """
        if self.connection_id is not None:
            raise Exception("Already received a connection id")
        
        await self.output.request_connection_id()
        self.logger.debug("Request for a connection id was sent")
        await self.await_event(Events.CONNECTION_ID_RECEIVED)

    async def join_game(self, game_id: str, slot: int = None):
        """Joins an already existing lobby with the given id

        :param game_id: Id of the game lobby to join to
        """
        if self.phase != GameStoragePhase.Start:
            raise Exception("Cannot join game when game is not in start phase")

        await self.output.join_lobby(game_id, slot=slot)

        # Ask for lobby changes and player readiness
        #self.interaction_buffer.put_nowait(GameInteractionType.CHANGE_LOBBY_PROPERTIES)
        #self.interaction_buffer.put_nowait(GameInteractionType.PLAYER_READY)

    async def create_new_lobby(
            self,
            scenario_id: Optional[int] = None, 
            options: Optional[Union[GameOptionsModel,Dict[str, int]]] = None
        ):
        """Creates a lobby with the given lobby info

        :param scenario_id: Id of the scenario to select
        :param options: Options to set for the game, that have key-values like
            the structure of a GameOptions object
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
            if isinstance(options, dict):
                game_options = GameOptionsModel.from_dict(options)
            elif isinstance(options, GameOptionsModel):
                game_options = options
            else:
                raise ValueError(f"unknown type '{type(options)}' for options")
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
        
        if amount <= 0: 
            return
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
    
    async def get_curr_phase(self) -> GamePhase:
        """Returns the current phase of the game

        :return: Current phase of the game
        """
        if self.game_state is None:
            return GamePhase.Starting
        return self.game_state.game_phase

    def _is_my_turn(self, current_phase: GamePhase) -> bool:
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
        if role is None: 
            return False

        if current_phase == GamePhase.InitDraw:
            return True

        if current_phase == GamePhase.DefenderPreSetup:
            return role.type == ActorType.DEFENCE

        if current_phase not in [GamePhase.Attacker, GamePhase.Defender]:
            return False
        
        is_attacker = role.type == ActorType.ATTACK and current_phase == GamePhase.Attacker
        is_defender = role.type ==  ActorType.DEFENCE and current_phase == GamePhase.Defender

        return is_attacker or is_defender

    def get_player_role(
            self,
            connection_id: Optional[str] = None
        ) -> ActorModel:
        """Returns the role of the agent's player (None) or with the given 
        connection id

        :param connection_id: Connection id of the player to get the role of
        :return: Role of the player or None if no role was found
        """
        if self.game_state is None or self.game_state.roles is None:
            return None

        return self.game_state.roles.get(
            connection_id or self.game_state.connection_id,
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
        
        actor_id = connection_id or self.game_state.connection_id
        if actor_id not in self.game_state.roles: return None

        self.game_state.roles[actor_id] = role

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
        self.logger.debug(f"Start interaction 'buying'")
        if self.phase != GameStoragePhase.Running:
            raise RuntimeError("Cannot shop when game is not running")
        if self.game_state is None:
            raise RuntimeError("Cannot start game if game state is not set")
        if not GameInteraction.is_interaction_valid(self.game_state, GameInteractionType.SHOPPING_PHASE): 
            raise RuntimeError(
                f"Wrong interaction phase: current interaction phase is "
                f"{self.game_state.interaction_phase} but a SHOPPING_PHASE "
                "was detected"
            )

        if len(equipment_ids) > 0:
            await self.output.buy_equipment(equipment_ids)
            await self.await_events(
                [Events.EQUIPMENT_CHANGED, Events.REMOVED_EQUIPMENT_FROM_SHOP]
            )

        self.game_state = GameInteraction.move_from_shopping(self.game_state)
        # next game interaction is PLAY_CARD
        await self._switch_to_play_card_git()
        
        self.logger.debug(f"Finished interaction 'buying'")
        # important for GIRS in Bot to check whether the operation was succesful
        # or it should select another action.
        return True

    async def finish_shopping(self):
        """Finishs the shopping phase for the agent

        :raises RuntimeError: GameStoragePhase is not 'running'
        :raises RuntimeError: game state is None
        :raises RuntimeError: GamePhase is not 'shopping'
        """
        self.logger.debug(f"Start interaction 'buying'")
        if self.phase != GameStoragePhase.Running:
            raise RuntimeError("Cannot shop when game is not running")
        if self.game_state is None:
            raise RuntimeError("Cannot start game if game state is not set")
        if not GameInteraction.is_interaction_valid(self.game_state, GameInteractionType.SHOPPING_PHASE): 
            raise RuntimeError(
                f"Wrong interaction phase: current interaction phase is "
                f"{self.game_state.interaction_phase} but a SHOPPING_PHASE "
                "was detected"
            )
            
        # No command for finishing shopping necessary anymore, as shopping is
        # not an official game phase anymore. Only the next game interaction 
        # changes.

        self.game_state = GameInteraction.move_from_shopping(self.game_state)
        # next game interaction is PLAY_CARD
        await self._switch_to_play_card_git()
        
        self.logger.debug(f"Finished interaction 'buying'")
        # important for GIRS in Bot to check whether the operation was succesful
        # or it should select another action.
        return True
    
    async def _handle_no_playable_action(self):
        """Handles what to do (leaving) if no playable action remains for the 
        agent to play
        """
        error_msg = f"Error {Errors.NoPlayableActionError}: no playable action available"
        if self.phase.value > GameStoragePhase.Start.value:
            # if this happens during pre-setup, skip the entire pre-
            # setup and continue the game
            if self.game_state.game_phase == GamePhase.DefenderPreSetup:
                self.logger.debug(error_msg)
                # Sending "preset done" is done by the bot/env not here
                # self.logger.debug("Skip pre-setup due to no other options")
                # await self.output.send_preset_done()
                # set offer_received back to False because preset is done and there
                # is no 'new_turn' message if there is an InitialDraw
                self.offer_received = False
            else:
                self.logger.error(error_msg)
                self.logger.error("Surrender due to no other options")
                await self.output.surrender()
                await self.leave_game()
                await self.close()

    async def play_action(
        self,
        action_idx: int,
        target_asset_id: int,
        attack_mask_idx: int,
        support_action_idxs: List[int] = None,
        equipment_idxs: List[int] = None,
        response_target_id: int = 0
    ) -> bool:
        """Plays an action this contains an card (main action), target asset, 
        attack mask, optional support actions and equipment

        :param action_id: Id of the action to play
        :param target_asset_id: Id of the target asset
        :param attack_mask: Mode of attack that the action aims at. 
            Possible Values: "C", "I", "A", "CI", "CA", "CIA"
        :param support_action_ids: List of support action ids. Starts with 0.
        :param equipment_ids: List of equipment ids. Starts with 0.
        :param response_target_id: Id of a previously played ID on the 
            target, the current main_action shall counter. Defaults to 0.
        """
        if self.game_state.actions_played_this_turn == 0:
            self.logger.debug("start interaction 'playing'")
        if not GameInteraction.is_interaction_valid(self.game_state, GameInteractionType.PLAY_CARD):
            raise RuntimeError(
                f"Wrong interaction phase: current interaction phase is "
                f"{self.game_state.interaction_phase} but a PLAY_CARD "
                "was detected"
            )

        if support_action_idxs is None:
            support_action_idxs = []
        if equipment_idxs is None:
            equipment_idxs = []

        # clear the switch for action point setting so that the first message
        # changes the action points
        self.play_action_finished.clear()

        main_action = self.game_state.hand[action_idx]
        new_target_asset_id = target_asset_id if target_asset_id != 0 else None
        attack_mask = VALID_ATTACK_MASKS[attack_mask_idx]
        if attack_mask == "" and main_action.predefined_attack_mask is not None:
            attack_mask = main_action.predefined_attack_mask
        support_action_ids = [
            self.game_state.hand[idx].id for idx in support_action_idxs
        ]
        equipment_ids = [
            self.game_state.equipment[idx].id
            for idx in equipment_idxs
        ]

        # send play action command to the server
        await self.output.play_action(
            main_action.id,
            new_target_asset_id,
            attack_mask,
            support_action_ids,
            equipment_ids,
            response_target_id
        )
        # await until the response of the server is received and executed
        success_reply = await self.await_event(Events.PLAY_ACTION_REPLY)
        successful = success_reply.get('successful', False)

        self.logger.debug(
            f"Play action {main_action.name} successful: {successful}"
        )
        # no need to remove played actions here, PenQuest server sends a
        # separate message for that

        # TODO Debugging why?
        if isinstance(successful, list):
            if len(successful) == 0:
                # multi-targeted action didn't find any target 
                successful = False
            else:
                successful = successful[0]

        actions_played = self.game_state.actions_played_this_turn
        self.game_state = dataclasses.replace(
            self.game_state,
            actions_played_this_turn=actions_played + 1
        )

        # In the last turn the turn is automatically finished afther the last
        # action is played.
        if self.game_state.role.ini == 1 and self.game_state.action_points == 0:
            await self.await_event(Events.PLAYER_ATTRIBUTE_CHANGED)

        # add another play card interaction to the buffer because players
        # can play multiple actions unless they chose to finish their turn
        # or they don't have enough action points anymore (especially in the
        # last turn!).
        if self.game_state.action_points > ActorHelper.get_min_aps(self.game_state.role):
            await self._switch_to_play_card_git()

        # free all waiting tasks to set new action points
        self.play_action_finished.set()
        # clear the switch so that the next message for action point updates
        # can set the changes between action plays
        self.play_action_finished.clear()

        return successful
    
    async def finish_turn(self):
        """Finishes the current game turn by sending a corresponding signal
        to the game server.
        """
        if not GameInteraction.is_interaction_valid(self.game_state, GameInteractionType.PLAY_CARD):
            raise RuntimeError(
                f"Wrong interaction phase: current interaction phase is "
                f"{self.game_state.interaction_phase} but a PLAY_CARD "
                "was detected"
            )

        self.shop_updated = False
        if self.game_state.game_phase == GamePhase.DefenderPreSetup:
            await self.output.send_preset_done()
            # set offer_received back to False because preset is done and there
            # is no 'new_turn' message if there is an InitialDraw
            self.offer_received = False
        else:
            await self.output.finish_turn()
        self.game_state = dataclasses.replace(
                self.game_state,
                validated_actions=None,
                playable_actions=None,
                actions_played_this_turn=0
            )

        # clear the switch 
        # in a regular case, a second message might flip the switch and if no
        # action is then played, then a regular ap update message gets trapped
        # in the switch
        self.play_action_finished.clear() 

        self.logger.debug(f"finished interaction 'playing'")
        return True
    
    async def selection_choose(self, action_ids: List):
        """the agents selection is forwarded to the PenQuest server

        :param action_ids: List of selected action IDs 
        :raises RuntimeError: GameStoragePhase is not 'running'
        :raises RuntimeError: game state is None
        :raises RuntimeError: agent doesn't have to select anything
        """
        self.logger.debug("start interaction 'redrawing'")
        if self.phase != GameStoragePhase.Running:
            raise RuntimeError("Cannot select actions when game is not running")
        if self.game_state is None:
            raise RuntimeError("Cannot select actions if game state is not set")
        if not GameInteraction.is_interaction_valid(self.game_state, GameInteractionType.CHOOSE_ACTION):
            raise RuntimeError(
                f"Wrong interaction phase: current interaction phase is "
                f"{self.game_state.interaction_phase} but a CHOOSE_ACTION "
                "was detected"
            )
        if not (self.game_state.selection_amount > 0 and len(self.game_state.selection_choices) > 0):
            raise RuntimeError(
                "Cannot select when player doesn't have anything to select from"
            )

        # Make selection and reset game state selection
        await self.output.select_actions(action_ids)
        await self.await_event(Events.ACTIONS_RECEIVED)
        self.game_state = dataclasses.replace(
            self.game_state, 
            selection_amount=-1,
            selection_choices=[]
        )
        # shop updates only during the game. If there is a defender pre-setup
        # then the shop was already sent at the beginning of the game, so no
        # need to wait for that event
        if self.game_state.game_options.equipment_shop_mode != EquipmentShopMode.DISABLED and \
            self.game_state.game_phase not in [GamePhase.DefenderPreSetup, GamePhase.InitDraw]:
            if not self.shop_updated:
                await self.await_event(Events.SHOP_UPDATED)
        self.game_state = GameInteraction.move_from_redrawing(self.game_state)

        if self._is_my_turn(self.game_state.game_phase) and \
            self.game_state.game_phase != GamePhase.InitDraw:
            if self.game_state.game_options.equipment_shop_mode > 0:
                self.interaction_buffer.put_nowait(
                    GameInteractionType.SHOPPING_PHASE
                )
            else:
                await self._switch_to_play_card_git()

        self.logger.debug("finished interaction 'redrawing'")
        # important for GIRS in Bot to check whether the operation was succesful
        # or it should select another action.
        return True

    async def do_nothing(self, *args, **kwargs):
        """Does literally nothing"""
        pass

    async def set_connection_id(self, connectionId:str):
        """Sets the connection ID of the environment

        :param connectionId: the new connection ID to be set
        """
        self.logger.debug(
            f"updated connection_id to: '{connectionId}'"
        )
        self.connection_id = connectionId
        if self.game_state is not None:
            self.game_state = dataclasses.replace(
                self.game_state,
                connection_id=connectionId
            )
        await self.dispatch_event(Events.CONNECTION_ID_RECEIVED)

    async def leave_game(self):
        """Leaves the current game and awaits until the PenQuest server confirms
        that the player left the game

        :raises RuntimeError: game state is None (no game to leave)
        """
        if self.lobby is None and self.game_state is None:
            raise RuntimeError("Nothing to leave")

        # only leave game if there was not already a leave game sent
        if self.leave_game_sent:
            return

        self.leave_game_sent = True
        await self.output.leave_game()
        await self.await_event(Events.GAME_LEFT)

    def is_over(self) -> bool:
        """Indicates whether the current game is over or not

        :return: game over flag
        """
        return self.phase == GameStoragePhase.Ended
