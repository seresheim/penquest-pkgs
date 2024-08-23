from typing import List, Dict
from dataclasses import dataclass

from penquest_pkgs.network.ProtocolParts import Required, Optional
from penquest_pkgs.constants.GameEndedState import GameEndedState
from penquest_pkgs.network.game_messages.message_models import(
    Player,
    GameOptions,
    ScenarioTeaser,
    Lobby,
    Equipment,
    EquipmentTemplate,
    ActionTemplate,
    Action,
    Asset,
    Game,
    Errors,
    ActionChanceModifier,
    AssetChanges,
    PostGameSummary,
    Playable,
    EventEntry,
)

@dataclass()
class InboundMessage():

    def __init__(self, **kwargs):
        pass


@dataclass()
class LobbyInfoMessage(InboundMessage):
    lobby = Required(Lobby)


@dataclass()
class ScenariosMessage(InboundMessage):
    """Obsolete"""
    scenarios = Required(List[ScenarioTeaser])


@dataclass()
class ScenarioChangedMessage(InboundMessage):
    """Obsolete"""
    scenario = Required(ScenarioTeaser)


@dataclass()
class UpdatePlayerMessage(InboundMessage):
    player = Required(Player)


@dataclass()
class PlayerReadyChangedMessage(InboundMessage):
    connection_id = Required(str)
    slot = Required(int)
    ready = Required(bool)
    player = Required(Player)


@dataclass()
class GameOptionsChangedMessage(InboundMessage):
    new_game_options = Required(GameOptions)


@dataclass()
class ChangeSlotsMessage(InboundMessage):
    connection_id = Required(str)
    new_slot = Required(int)
    old_slot = Required(int)


@dataclass()
class PlayerEnteredMessage(InboundMessage):
    player = Required(Player)
    slot = Required(int)


@dataclass()
class PlayerLeftMessage(InboundMessage):
    player = Required(Player)
    slot = Required(int)


@dataclass()
class GotKickedMessage(InboundMessage):
    pass


@dataclass()
class GamePlayerChangedMessage(InboundMessage):
    new_connection_id = Required(str)
    new_player_id = Optional(int, nullable=True)
    old_connection_id = Required(str)
    old_player_id = Optional(int, nullable=True)
    player = Required(Player)


@dataclass()
class GameStartedMessage(InboundMessage):
    game = Required(Game)


@dataclass()
class GameStateMessage(InboundMessage):
    game = Required(Game)


@dataclass()
class GamePhaseChangedMessage(InboundMessage):
    game_phase = Required(str)


@dataclass()
class AssortmentReceivedMessage(InboundMessage):
    equipment = Required(List[EquipmentTemplate])


@dataclass()
class AttributeChangedMessage(InboundMessage):
    attribute = Required(str)
    value = Required(float)


@dataclass()
class EquipmentReceivedMessage(InboundMessage):
    equipment = Required(List[Equipment])


@dataclass()
class ActionPlayableMessage(InboundMessage):
    detectionModifier = Required(List[ActionChanceModifier])
    detection_chance = Required(float)
    errors = Optional(Errors)
    playable = Required(bool)
    response_target_ids = Required(List[int])
    successModifier = Required(List[ActionChanceModifier])
    success_chance = Required(float)


@dataclass()
class RemoveCardsMessage(InboundMessage):
    actionIds = Required(List[int])
    equipmentIds = Required(List[int])


@dataclass()
class ActionsDetectedMessage(InboundMessage):
    actions = Required(List[Action])


@dataclass()
class ActionSuccessfulMessage(InboundMessage):
    action = Required(Action)
    successful = Required(bool)


@dataclass()
class OfferSelectionMessage(InboundMessage):
    actions = Required(List[ActionTemplate])
    amount_selection = Required(int)


@dataclass()
class ActionsReceivedMessage(InboundMessage):
    new_actions = Required(List[Action])


@dataclass()
class AssetChangedMessage(InboundMessage):
    asset = Required(Asset)


@dataclass()
class AssetChangesMessage(InboundMessage):
    asset_changes = Required(AssetChanges)


@dataclass()
class GameEndedMessage(InboundMessage):
    endState = Required(GameEndedState)
    endMessage = Required(str)
    postGameSummary = Required(PostGameSummary)


@dataclass()
class AllActionsPlayableMessage(InboundMessage):
    playable_results=Required(Dict[int, Playable])


@dataclass()
class LobbyLeftMessage(InboundMessage):
    player=Optional(Player)


@dataclass
class GameCrashedMessage(InboundMessage):
    reason=Required(str)
    code=Required(int)


@dataclass
class GameTurnChangedMessage(InboundMessage):
    currentTurn=Required(int)


@dataclass
class NewConnectionIDMessage(InboundMessage):
    connectionId=Required(str)


@dataclass
class EventLogUpdatedMessage(InboundMessage):
    events = Required(List[EventEntry], nullable=True)


@dataclass
class RemoveEquipmentFromShopMessage(InboundMessage):
    equipmentIds = Required(List[str])


@dataclass
class ActorDetectedMessage(InboundMessage):
    actorId = Required(int)


@dataclass
class GameLeftMessage(InboundMessage):
    pass