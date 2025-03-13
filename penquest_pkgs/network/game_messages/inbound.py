from typing import List, Dict
from dataclasses import dataclass

from penquest_pkgs.network.ProtocolParts import Required, Optional
from penquest_pkgs.constants.GameEndedState import GameEndedState
from penquest_pkgs.network.game_messages.message_models import(
    PlayerMessageModel,
    GameOptionsMessageModel,
    ScenarioTeaserMessageModel,
    LobbyMessageModel,
    EquipmentMessageModel,
    EquipmentTemplateMessageModel,
    ActionTemplateMessageModel,
    ActionMessageModel,
    AssetMessageModel,
    GameMessageModel,
    ErrorsMessageModel,
    ActionChanceModifierMessageModel,
    AssetChangesMessageModel,
    PostGameSummaryMessageModel,
    PlayableMessageModel,
    EventEntryMessageModel,
)

@dataclass()
class InboundMessage():

    def __init__(self, **kwargs):
        pass


@dataclass
class NewConnectionIDMessage(InboundMessage):
    connectionId=Required(str)


@dataclass()
class LobbyInfoMessage(InboundMessage):
    lobby = Required(LobbyMessageModel)


@dataclass()
class PlayerEnteredMessage(InboundMessage):
    player = Required(PlayerMessageModel)
    slot = Required(int)


@dataclass()
class PlayerLeftMessage(InboundMessage):
    player = Required(PlayerMessageModel)
    slot = Required(int)


@dataclass()
class ScenariosMessage(InboundMessage):
    """Obsolete"""
    scenarios = Required(List[ScenarioTeaserMessageModel])


@dataclass()
class ScenarioChangedMessage(InboundMessage):
    """Obsolete"""
    scenario = Required(ScenarioTeaserMessageModel)


@dataclass()
class GameOptionsChangedMessage(InboundMessage):
    new_game_options = Required(GameOptionsMessageModel)


@dataclass()
class PlayerReadyChangedMessage(InboundMessage):
    connection_id = Required(str)
    slot = Required(int)
    ready = Required(bool)
    player = Required(PlayerMessageModel)


@dataclass()
class ChangeSlotsMessage(InboundMessage):
    connection_id = Required(str)
    new_slot = Required(int)
    old_slot = Required(int)


@dataclass()
class LobbyLeftMessage(InboundMessage):
    player=Optional(PlayerMessageModel)


@dataclass
class GameCrashedMessage(InboundMessage):
    reason=Required(str)
    code=Required(int)


@dataclass()
class GameStartedMessage(InboundMessage):
    game = Required(GameMessageModel)


@dataclass()
class GamePhaseChangedMessage(InboundMessage):
    game_phase = Required(str)


@dataclass()
class AttributeChangedMessage(InboundMessage):
    attribute = Required(str)
    value = Required(float)


@dataclass()
class AssortmentReceivedMessage(InboundMessage):
    equipment = Required(List[EquipmentTemplateMessageModel])


@dataclass()
class EquipmentReceivedMessage(InboundMessage):
    equipment = Required(List[EquipmentMessageModel])


@dataclass()
class ActionPlayableMessage(InboundMessage):
    detectionModifier = Required(List[ActionChanceModifierMessageModel])
    detection_chance = Required(float)
    errors = Optional(ErrorsMessageModel)
    playable = Required(bool)
    response_target_ids = Required(List[int])
    successModifier = Required(List[ActionChanceModifierMessageModel])
    success_chance = Required(float)


@dataclass()
class RemoveCardsMessage(InboundMessage):
    actionIds = Required(List[int])
    equipmentIds = Required(List[int])


@dataclass()
class ActionsDetectedMessage(InboundMessage):
    actions = Required(List[ActionMessageModel])


@dataclass()
class ActionSuccessfulMessage(InboundMessage):
    action = Required(ActionMessageModel)
    successful = Required(bool)


@dataclass()
class OfferSelectionMessage(InboundMessage):
    actions = Required(List[ActionTemplateMessageModel])
    amount_selection = Required(int)


@dataclass()
class ActionsReceivedMessage(InboundMessage):
    actions = Required(List[ActionMessageModel])


@dataclass()
class AssetChangedMessage(InboundMessage):
    asset = Required(AssetMessageModel)


@dataclass()
class AssetChangesMessage(InboundMessage):
    asset_changes = Required(AssetChangesMessageModel)


@dataclass
class GameTurnChangedMessage(InboundMessage):
    currentTurn=Required(int)


@dataclass()
class UpdatePlayerMessage(InboundMessage):
    player = Required(PlayerMessageModel)


@dataclass()
class GotKickedMessage(InboundMessage):
    pass


@dataclass()
class GamePlayerChangedMessage(InboundMessage):
    new_connection_id = Required(str)
    new_player_id = Optional(int, nullable=True)
    old_connection_id = Required(str)
    old_player_id = Optional(int, nullable=True)
    player = Required(PlayerMessageModel)


@dataclass()
class GameStateMessage(InboundMessage):
    game = Required(GameMessageModel)


@dataclass()
class GameEndedMessage(InboundMessage):
    endState = Required(int)
    endMessage = Required(str)
    postGameSummary = Required(PostGameSummaryMessageModel)


@dataclass
class GameLeftMessage(InboundMessage):
    pass


@dataclass
class EventLogUpdatedMessage(InboundMessage):
    events = Required(List[EventEntryMessageModel], nullable=True)


@dataclass
class RemoveEquipmentFromShopMessage(InboundMessage):
    equipmentIds = Required(List[str])


@dataclass
class ActorDetectedMessage(InboundMessage):
    actorId = Required(int)


@dataclass
class ActionPointsChangedMessage(InboundMessage):
    actionPoints = Required(int)


@dataclass()
class AllActionsPlayableMessage(InboundMessage):
    playable_results=Required(Dict[int, PlayableMessageModel])


@dataclass
class Errors(InboundMessage):
    error_id=Required(List[int])
    error_message=Required(List[str])
    multiple_errors=Required(bool)









