import asyncio
import traceback
from typing import Any, Dict, TypeVar, Union

import penquest_pkgs.network.game_messages.inbound as InboundMessages
from penquest_pkgs.network.PQPParser import PQPParser
from penquest_pkgs.utils.ios import parse_stream, parse_queue
from penquest_pkgs.constants import GameStoragePhase
from penquest_pkgs.mappers.inbound_mappers import(
    DefaultMapper,
    LobbyInfoMapper,
    ScenariosMapper,
    ScenarioChangedMapper,
    GameOptionsChangedMapper,
    PlayerMessageMapper,
    GameMessageMapper,
    EquipmentTemplatesMessageMapper,
    EquipmentsMessageMapper,
    ActionPlayableMapper,
    ActionMessageMapper,
    ActionsMessageMapper,
    ActionTemplatesMessageMapper,
    AssetMessageMapper,
    AssetChangesMessageMapper,
    GameEndedMapper,
    EventLogUpdateMapper,
    ErrorsMapper,
)


T = TypeVar('T')


class InputEvents:
    """Events that come as inputs over the network from the server
    """
     # Connection Commands
    NEW_CONNECTION_ID   = 'new_connection_id'  # a new mapping from our connection id to the internal connection id

    # Lobby Events
    LOBBY_INFO                  = 'lobby_info'              # Event to set the lobby information
    PLAYER_ENTERED              = 'player_entered'          # Event to set the player information for a slot
    PLAYER_LEFT                 = 'player_left'             # Event to set the player information for a slot
    SCENARIOS                   = 'scenarios'               # Event that lists all available scenarios
    SCENARIO_CHANGED            = 'scenario_changed'        # Event to set the scenario
    GAME_OPTIONS_CHANGED        = 'game_options_changed'    # Event to set the game options
    PLAYER_READY_CHANGED        = 'player_ready_changed'
    CHANGE_SLOTS                = 'changed_slots'
    GOT_KICKED                  = 'got_kicked'
    LOBBY_LEFT                  = 'lobby_left'
    GOT_KICKED                  = 'got_kicked'
    GAME_CRASHED                = 'game_crashed'

    # Game Events
    GAME_STARTED                = 'game_started'            # Event to indicate that the game has started
    GAME_PHASE_CHANGED          = 'game_phase_changed'      # Event to set the current game phase
    GAME_ENDED                  = 'game_ended'              # Event to indicate that the game has ended
    GAME_PLAYERS                = 'game_players'            # Event to set the players and their roles
    ATTRIBUTE_CHANGED           = 'attribute_changed'       # Event to set the players attributes
    ASSORTMENT_RECEIVED         = 'assortment_received'     # Event to set the assortment (cards of the shop)
    EQUIPMENT_RECEIVED          = 'equipment_received'      # Event to set the equipment (hand cards)
    ACTION_PLAYABLE             = 'action_playable'
    REMOVE_CARDS                = 'remove_cards'
    ACTIONS_DETECTED            = 'actions_detected'        # Event to set the actions that were detected
    ACTION_SUCCESS              = 'action_success'          # Reply from the backend that the action was successful
    OFFER_SELECTION             = 'offer_selection'         # Event to set a offer selection like drawing a card 
    ACTIONS_RECEIVED            = 'actions_received'        # Reply to set the actions that were received after chosing in a selection offering (like drawing) 
    ASSET_CHANGED               = 'asset_changed'           # Event to set the information of an asset
    ASSET_CHANGES               = 'asset_changes'           # Event to set the info of multiple assets
    UPDATE_PLAYER               = 'update_player'
    GAME_PLAYER_CHANGED         = 'game_player_changed'
    GAME_STATE                  = 'game_state'
    GAME_TURN_CHANGED           = 'game_turn_changed'
    GAME_LEFT                   = 'game_left'
    EVENTLOG_UPDATED            = 'eventlog_updated'
    REMOVE_EQUIPMENT_FROM_SHOP  = 'remove_equipment_from_shop'      # Sends a list of equipment ids to remove from the shop
    ACTOR_DETECTED              = 'actor_detected'          # Event to set 'hasBeenDetected' attribute for actors
    ACTION_POINTS_CHANGED       = 'action_points_changed'   # Event to set the action points of a player

    ALL_ACTIONS_PLAYABLE        = 'all_actions_playable'    # Reply from the backend that contains all actions that are playable

    # Other Events
    ERROR                       = 'error'


EVENT_MESSAGE_MAPPING = {
    InputEvents.NEW_CONNECTION_ID: InboundMessages.NewConnectionIDMessage,
    InputEvents.LOBBY_INFO: InboundMessages.LobbyInfoMessage,
    InputEvents.PLAYER_ENTERED: InboundMessages.PlayerEnteredMessage,
    InputEvents.PLAYER_LEFT: InboundMessages.PlayerLeftMessage,
    InputEvents.SCENARIOS: InboundMessages.ScenariosMessage,
    InputEvents.SCENARIO_CHANGED: InboundMessages.ScenarioChangedMessage,
    InputEvents.GAME_OPTIONS_CHANGED: InboundMessages.GameOptionsChangedMessage,
    InputEvents.PLAYER_READY_CHANGED: InboundMessages.PlayerReadyChangedMessage,
    InputEvents.CHANGE_SLOTS: InboundMessages.ChangeSlotsMessage,
    InputEvents.LOBBY_LEFT: InboundMessages.LobbyLeftMessage,
    InputEvents.GAME_CRASHED: InboundMessages.GameCrashedMessage,
    InputEvents.GAME_STARTED: InboundMessages.GameStartedMessage,
    InputEvents.GAME_PHASE_CHANGED: InboundMessages.GamePhaseChangedMessage,
    InputEvents.ATTRIBUTE_CHANGED: InboundMessages.AttributeChangedMessage,
    InputEvents.ASSORTMENT_RECEIVED: InboundMessages.AssortmentReceivedMessage,
    InputEvents.EQUIPMENT_RECEIVED: InboundMessages.EquipmentReceivedMessage,
    InputEvents.ACTION_PLAYABLE: InboundMessages.ActionPlayableMessage,
    InputEvents.REMOVE_CARDS: InboundMessages.RemoveCardsMessage,
    InputEvents.ACTIONS_DETECTED: InboundMessages.ActionsDetectedMessage,
    InputEvents.ACTION_SUCCESS: InboundMessages.ActionSuccessfulMessage,
    InputEvents.OFFER_SELECTION: InboundMessages.OfferSelectionMessage,
    InputEvents.ACTIONS_RECEIVED: InboundMessages.ActionsReceivedMessage,
    InputEvents.ASSET_CHANGED: InboundMessages.AssetChangedMessage,
    InputEvents.ASSET_CHANGES: InboundMessages.AssetChangesMessage,
    InputEvents.GAME_TURN_CHANGED: InboundMessages.GameTurnChangedMessage,
    InputEvents.UPDATE_PLAYER: InboundMessages.UpdatePlayerMessage,
    InputEvents.GOT_KICKED: InboundMessages.GotKickedMessage,
    InputEvents.GAME_PLAYER_CHANGED: InboundMessages.GamePlayerChangedMessage,
    InputEvents.GAME_STATE: InboundMessages.GameStateMessage,
    InputEvents.GAME_ENDED: InboundMessages.GameEndedMessage,
    InputEvents.GAME_LEFT: InboundMessages.GameLeftMessage,
    InputEvents.EVENTLOG_UPDATED: InboundMessages.EventLogUpdatedMessage,
    InputEvents.REMOVE_EQUIPMENT_FROM_SHOP: InboundMessages.RemoveEquipmentFromShopMessage,
    InputEvents.ACTOR_DETECTED: InboundMessages.ActorDetectedMessage,
    InputEvents.ACTION_POINTS_CHANGED: InboundMessages.ActionPointsChangedMessage,
    InputEvents.ALL_ACTIONS_PLAYABLE: InboundMessages.AllActionsPlayableMessage,
    InputEvents.ERROR: InboundMessages.Errors
}

EVENT_MAPPERS = {
    InputEvents.NEW_CONNECTION_ID: DefaultMapper,
    InputEvents.LOBBY_INFO: LobbyInfoMapper,
    InputEvents.PLAYER_ENTERED: PlayerMessageMapper,
    InputEvents.PLAYER_LEFT: PlayerMessageMapper,
    InputEvents.SCENARIOS: ScenariosMapper,
    InputEvents.SCENARIO_CHANGED: ScenarioChangedMapper,
    InputEvents.GAME_OPTIONS_CHANGED: GameOptionsChangedMapper,
    InputEvents.PLAYER_READY_CHANGED: PlayerMessageMapper,
    InputEvents.CHANGE_SLOTS: DefaultMapper,
    InputEvents.LOBBY_LEFT: PlayerMessageMapper,
    InputEvents.GAME_CRASHED: DefaultMapper,
    InputEvents.GAME_STARTED: GameMessageMapper,
    InputEvents.GAME_PHASE_CHANGED: DefaultMapper,
    InputEvents.ATTRIBUTE_CHANGED: DefaultMapper,
    InputEvents.ASSORTMENT_RECEIVED: EquipmentTemplatesMessageMapper,
    InputEvents.EQUIPMENT_RECEIVED: EquipmentsMessageMapper,
    InputEvents.ACTION_PLAYABLE: ActionPlayableMapper,
    InputEvents.REMOVE_CARDS: DefaultMapper,
    InputEvents.ACTIONS_DETECTED: ActionsMessageMapper,
    InputEvents.ACTION_SUCCESS: ActionMessageMapper,
    InputEvents.OFFER_SELECTION: ActionTemplatesMessageMapper,
    InputEvents.ACTIONS_RECEIVED: ActionsMessageMapper,
    InputEvents.ASSET_CHANGED: AssetMessageMapper,
    InputEvents.ASSET_CHANGES: AssetChangesMessageMapper,
    InputEvents.GAME_TURN_CHANGED: DefaultMapper,
    InputEvents.UPDATE_PLAYER: PlayerMessageMapper,
    InputEvents.GOT_KICKED: DefaultMapper,
    InputEvents.GAME_PLAYER_CHANGED: PlayerMessageMapper,
    InputEvents.GAME_STATE: GameMessageMapper,
    InputEvents.GAME_ENDED: GameEndedMapper,
    InputEvents.GAME_LEFT: DefaultMapper,
    InputEvents.EVENTLOG_UPDATED: EventLogUpdateMapper,
    InputEvents.REMOVE_EQUIPMENT_FROM_SHOP: DefaultMapper,
    InputEvents.ACTOR_DETECTED: DefaultMapper,
    InputEvents.ACTION_POINTS_CHANGED: DefaultMapper,
    InputEvents.ERROR: ErrorsMapper,
}

NON_PARSABLE_MESSAGES = {
    InputEvents.GOT_KICKED,
    InputEvents.GAME_PLAYERS
}

class GameInputInterpreter:
    """
    This class interprets the messages received from the backend and calls the 
    corresponding functions in the game.
    This is done for the following reasons:
    - Filtering out unnecessary information for the frontend client
    - Converting the data into the correct dataclass datatype
    - Mapping the game commands into the correct game functions
    - Limiting the functionality the remote server can call to only the 
        functions that are needed
    - Providing a simple interface to manage the remote input into the game
    """


    def __init__(
            self, 
            input_channel: Union[asyncio.StreamReader, asyncio.Queue], 
            game = None
        ):
        """Initializes the input interpreter 
        """
        if isinstance(input_channel, asyncio.StreamReader):
            input_channel = parse_stream(input_channel)
        elif isinstance(input_channel, asyncio.Queue):
            input_channel = parse_queue(input_channel)
        self.input_channel = input_channel
        self.listening_job = None
        self.set_game(game)

    def set_game(self, game):
        """Set the game instance that should be used for the input interpreter

        :param game: game instance that is set
        """
        self.game = game

        if game is None: 
            self.events = {}
            return
        
        # Cannot import Game due to circular import (maybe the overall 
        # archtiecture should be changed)
        self.events = {
            # Connection Events
            InputEvents.NEW_CONNECTION_ID: self.game.set_connection_id,

            # Lobby Events
            InputEvents.LOBBY_INFO: self.game.input.set_lobby_information,
            InputEvents.PLAYER_ENTERED: self.game.input.set_lobby_player_information_for_slot,
            InputEvents.PLAYER_LEFT: self.game.input.remove_player,
            InputEvents.SCENARIO_CHANGED: self.game.input.set_scenario,
            InputEvents.GAME_OPTIONS_CHANGED: self.game.input.update_game_options,
            InputEvents.PLAYER_READY_CHANGED: self.game.do_nothing,
            InputEvents.CHANGE_SLOTS: self.game.input.changed_slots,
            InputEvents.LOBBY_LEFT: self.game.input.lobby_left,
            InputEvents.GOT_KICKED: self.game.input.got_kicked,
            InputEvents.GAME_CRASHED: self.game.input.game_crashed,

            # Game Events
            InputEvents.GAME_STARTED: self.game.input.start_game,
            InputEvents.GAME_PLAYERS: self.game.do_nothing,
            InputEvents.ATTRIBUTE_CHANGED: self.game.input.set_player_attribute,
            InputEvents.ASSORTMENT_RECEIVED: self.game.input.set_assortment,
            InputEvents.EQUIPMENT_RECEIVED: self.game.input.add_equipment,
            InputEvents.GAME_PHASE_CHANGED: self.game.input.set_game_phase,
            InputEvents.ACTION_SUCCESS: self.game.input.played_action_reply,
            InputEvents.ACTIONS_DETECTED: self.game.input.add_actions_detected_event,
            InputEvents.ASSET_CHANGED: self.game.input.update_asset,
            InputEvents.ASSET_CHANGES: self.game.input.update_assets,
            InputEvents.OFFER_SELECTION: self.game.input.set_received_offering,
            InputEvents.ACTIONS_RECEIVED: self.game.input.add_new_actions_to_hand,
            InputEvents.REMOVE_CARDS: self.game.input.remove_cards,
            InputEvents.GAME_TURN_CHANGED: self.game.input.game_turn_changed,
            InputEvents.UPDATE_PLAYER: self.game.input.update_player,
            InputEvents.GAME_PLAYER_CHANGED: self.game.input.game_player_changed,
            InputEvents.GAME_STATE: self.game.input.update_game_state,
            InputEvents.GAME_ENDED: self.game.input.game_ended,
            InputEvents.GAME_LEFT: self.game.input.game_left,
            InputEvents.REMOVE_EQUIPMENT_FROM_SHOP: self.game.input.remove_equipment_from_shop,
            InputEvents.ACTOR_DETECTED: self.game.input.actor_detected,
            InputEvents.ACTION_POINTS_CHANGED: self.game.input.action_points_changed,
            InputEvents.EVENTLOG_UPDATED: self.game.do_nothing,

            # Other Events
            InputEvents.ERROR: self.game.input.error,
        }
        
        

    # Game Input Interpreter
    def interpret(self, msg: Dict[str, Any]):
        """Interpret the messages that came from the network and 
        call the corresponding methods

        Args:
            msg (Dict[str, Any]): message coming from the network
        """
        parser = PQPParser()

        event = msg.get('event', None)
        data = msg.get("data", {})
        message_obj = object()

        if event is None: 
            return
        elif event in EVENT_MESSAGE_MAPPING:
            try:
                message_obj = parser.parse_message(
                    data, 
                    EVENT_MESSAGE_MAPPING[event]
                )
            except Exception as e:
                logger = self.game.logger
                logger.error(f"Error while parsing event '{event}': {e}")
                traceback.print_exc()
        elif event in NON_PARSABLE_MESSAGES:
            message_obj = object()
        else:
            logger = self.game.logger
            logger.warning(
                f"Unknown event '{event}' received. With data: {data}"
            )
        # Create a separate task for each message handling, because then
        # messages can await for the arrival of other messages first. Otherwise
        # the single task that handles all messages is blocked by the waiting
        # message and the other incoming message that is waited for is stuck.
        task = asyncio.create_task(
            self.new_task_intro(event, message_obj)
        )
        current_name = task.get_name().split("-")
        task.set_name(f"Task-{current_name[-1]}({event})")

    async def new_task_intro(self, event: str,  message_obj: InboundMessages.InboundMessage):
        """This is the intro for all handling routine tasks. It's purpose is to
        catch all exceptions that are thrown in the handling routine and log
        them. This is necessary because otherwise the task would be cancelled
        and the exception would be lost.

        :param event: name of the event that needs handling
        :param message_dict: message that should be handled
        """
        self.game.logger.debug(f"handle message '{event}'")
        try:
            mapped_message = EVENT_MAPPERS[event].map(message_obj)
            mapped_message_dict = {
                    key: value 
                    for key, value in mapped_message.__dict__.items() 
                    if not key.startswith("__")
                }
            handling_coroutine = self.events.get(event, self.game.do_nothing)
            await handling_coroutine(**mapped_message_dict)
        except asyncio.CancelledError:
            if self.game.phase == GameStoragePhase.Running:
                self.game.logger.error(
                    f"Task for event '{event}' was cancelled while the game was"
                    f" still running"
                )
        except Exception as e:
            self.game.logger.error(
                f"Error while interpreting event '{event}': {e}"
            )
            traceback.print_exc()
        finally:
            self.game.logger.debug(f"finished handling '{event}'")
        


    # Listening Jobs
    async def listen_to_messages(self, established_event: asyncio.Event, game = None):
        self.set_game(game)
        established_event.set()
        self.game.logger.log(5, "Listening for incoming messages")
        async for msg in self.input_channel:
            if msg is None: break
            self.game.logger.log(5, f"Received message: {msg}")
            self.interpret(msg)

