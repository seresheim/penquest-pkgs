from penquest_pkgs.network.game_messages.inbound import (
    InboundMessage,
    LobbyInfoMessage,
    ScenariosMessage,
    ScenarioChangedMessage,
    UpdatePlayerMessage,
    GameOptionsChangedMessage,
    GameStartedMessage,
    AssortmentReceivedMessage,
    ActionPlayableMessage,
    AssetChangesMessage,
    GameEndedMessage,
    AllActionsPlayableMessage,
    EventLogUpdatedMessage,
)
from penquest_pkgs.mappers.message_model_mappers import (
    LobbyMapper,
    ScenarioTeaserMapper,
    PlayerMapper,
    GameOptionsMapper,
    GameMapper,
    EquipmentTemplateMapper,
    EquipmentMapper,
    ActionChanceModifierMapper,
    ErrorsMapper,
    ActionMapper,
    ActionTemplateMapper,
    AssetMapper,
    AssetChangesMapper,
    PostGameSummaryMapper,
    EventEntryMapper,
)


class DefaultMapper():

    @classmethod
    def map(cls, message: InboundMessage):
        return message


class LobbyInfoMapper():

    @classmethod
    def map(cls, message: LobbyInfoMessage):
        message.lobby = LobbyMapper.map(message.lobby)
        return message
    

class ScenariosMapper():

    @classmethod
    def map(cls, message: ScenariosMessage) -> ScenariosMessage:
        message.scenarios = [ScenarioTeaserMapper.map(s) for s in message.scenarios]
        return message


class ScenarioChangedMapper():

    @classmethod
    def map(cls, message: ScenarioChangedMessage) -> ScenarioChangedMessage:
        message.scenario = PlayerMapper.map(message.scenario)
        return message


class UpdatePlayerMapper():

    @classmethod
    def map(cls, message: UpdatePlayerMessage) -> UpdatePlayerMessage:
        message.player = PlayerMapper.map(message.player)
        return message
    

class GameOptionsChangedMapper():

    @classmethod
    def map(cls, message: GameOptionsChangedMessage) -> GameOptionsChangedMessage:
        message.new_game_options = GameOptionsMapper.map(message.new_game_options)
        return message
    

class PlayerMessageMapper():

    @classmethod
    def map(cls, message):
        message.player = PlayerMapper.map(message.player)
        return message
    

class GameMessageMapper():

    @classmethod
    def map(cls, message: GameStartedMessage) -> GameStartedMessage:
        message.game = GameMapper.map(message.game)
        return message
    

class EquipmentTemplateMessageMapper():

    @classmethod
    def map(cls, message):
        message.equipment =EquipmentTemplateMapper.map(message.equipment)
        return message


class EquipmentTemplatesMessageMapper():

    @classmethod
    def map(cls, message):
        message.equipment = [EquipmentTemplateMapper.map(eq_t) for eq_t in message.equipment]
        return message
    

class EquipmentMessageMapper():

    @classmethod
    def map(cls, message: AssortmentReceivedMessage) -> AssortmentReceivedMessage:
        message.equipment = EquipmentMapper.map(message.equipment)
        return message
    

class EquipmentsMessageMapper():

    @classmethod
    def map(cls, message: AssortmentReceivedMessage) -> AssortmentReceivedMessage:
        message.equipment = [EquipmentMapper.map(eq) for eq in message.equipment]
        return message

class ActionPlayableMapper():

    @classmethod
    def map(cls, message: ActionPlayableMessage) -> ActionPlayableMessage:
        message.detection_modifier = ActionChanceModifierMapper.map(message.detectionModifier)
        del message.detectionModifier
        message.errors = ErrorsMapper.map(message.errors)
        message.success_modifier = ActionChanceModifierMapper.map(message.successModifier)
        del message.successModifier
        return message
    
class ActionMessageMapper():

    @classmethod
    def map(cls, message):
        message.action = ActionMapper.map(message.action)
        return message
    

class ActionsMessageMapper():

    @classmethod
    def map(cls, message):
        message.actions = [ActionMapper.map(action) for action in message.actions]
        return message
    

class ActionTemplateMessageMapper():

    @classmethod
    def map(cls, message):
        message.action = ActionTemplateMapper.map(message.action)
        return message
    

class ActionTemplatesMessageMapper():

    @classmethod
    def map(cls, message):
        message.actions = [ActionTemplateMapper.map(action) for action in message.actions]
        return message
    

class AssetMessageMapper():

    @classmethod
    def map(cls, message):
        message.asset = AssetMapper.map(message.asset)
        return message


class AssetChangesMessageMapper():

    @classmethod
    def map(cls, message: AssetChangesMessage):
        message.asset_changes = AssetChangesMapper.map(message.asset_changes)
        return message
    

class GameEndedMapper():

    @classmethod
    def map(cls, message: GameEndedMessage):
        message.post_game_summary = PostGameSummaryMapper.map(message.postGameSummary)
        del message.postGameSummary

        message.end_state = message.endState
        del message.endState

        message.end_message = message.endMessage
        del message.endMessage
        return message
    
class EventLogUpdateMapper():

    @classmethod
    def map(cls, message: EventLogUpdatedMessage):
        message.events = [EventEntryMapper.map(event) for event in message.events]
        return message