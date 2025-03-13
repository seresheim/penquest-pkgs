from penquest_pkgs.network.ProtocolParts import Required, Optional, Options
from penquest_pkgs.constants.GameEndedState import GameEndedState
from typing import List, Dict, Union
from dataclasses import dataclass


@dataclass()
class PlayerMessageModel():
    id: int = Required(int)
    connection_id: str = Required(str)
    avatar_id: str = Required(str, nullable=True)
    name: str = Required(str)
    online: bool = Required(bool)
    user_id: str = Required(str)
    rank: int = Required(int)


@dataclass
class GameOptionsMessageModel:
    action_detection_mode: int = Required(int)
    action_shop_mode: int = Required(int)
    action_success_mode: int = Required(int)
    initial_action_mode: int = Required(int)
    initial_asset_stage: int = Required(int)
    manual_def_type_mode: int = Required(int)
    support_actions_mode: int= Required(int)
    equipment_shop_mode: int= Required(int)
    infiniteShields: int= Required(int)
    multiTargetSuccess: int= Required(int)
    defenderActionsDetectable: int= Required(int)
    availabilityPenalty: int= Required(int)
    defenderPreSetupMode: int= Required(int)


@dataclass()
class GameOptionLocksMessageModel():
    action_detection_mode: bool = Required(bool)
    action_shop_mode: bool = Required(bool)
    action_success_mode: bool = Required(bool)
    initial_action_mode: bool = Required(bool)
    initial_asset_stage: bool = Required(bool)
    manual_def_type_mode: bool = Required(bool)
    support_actions_mode: bool = Required(bool)
    equipment_shop_mode: bool = Required(bool)
    infiniteShields: bool = Required(bool)
    multiTargetSuccess: bool = Required(bool)
    defenderActionsDetectable: bool = Required(bool)
    availabilityPenalty: bool = Required(bool)
    defenderPreSetupMode: bool= Required(bool)


@dataclass()
class SlotInfoMessageModel():
    slotId: int = Required(int)
    name: str = Required(str)
    type: int = Required(int)
    isReady: bool = Required(bool)


@dataclass()
class ScenarioTeaserMessageModel():
    id: str = Required(str)
    name: str = Required(str)
    description: str = Required(str)
    availableSlots: List[SlotInfoMessageModel] = Required(List[SlotInfoMessageModel])


@dataclass
class GoalDescMessageModel():
    id: str = Required(str)
    description: str = Required(str)
    isDefault: bool = Required(bool)


@dataclass()
class LobbyMessageModel():
    admin: PlayerMessageModel = Required(PlayerMessageModel)
    code: str = Required(str)
    players: Dict[int, PlayerMessageModel] = Required(Dict[int, PlayerMessageModel], nullable=True)
    scenario: ScenarioTeaserMessageModel = Required(ScenarioTeaserMessageModel, nullable=True)
    game_options: GameOptionsMessageModel = Required(GameOptionsMessageModel)
    gameOptionLocks: GameOptionLocksMessageModel = Required(GameOptionLocksMessageModel)
    availableGoals: List[GoalDescMessageModel] = Required(List[GoalDescMessageModel], nullable=True)
    xpEvent: str = Required(str, nullable=True)
    seed: int = Required(int, nullable=True)


@dataclass()
class EffectMessageModel():
    id: int = Required(int)
    type: int = Required(int)
    name: str = Required(str)
    description: str = Required(str)
    owner_id: int = Required(int, nullable=True)
    scope: str = Required(str, nullable=True)
    active: bool = Optional(bool, nullable=True)
    attributes: List[str] = Optional(List[str], nullable=True)
    equipment: List["EquipmentTemplateMessageModel"] = Optional(List["EquipmentTemplateMessageModel"], nullable=True)
    num_effects: int = Optional(int, nullable=True)
    probability: float = Optional(float, nullable=True)
    turns: int = Optional(int, nullable=True)
    value: float = Optional(float, nullable=True)
    isPermanent: bool = Required(bool)
    #effectType: int = Required(int)


@dataclass()
class EquipmentTemplateMessageModel():
    id: str = Required(str)
    type: str = Required(str)
    name: str = Required(str)
    short_description: str = Required(str)
    long_description: str = Required(str)
    impact: List[int] = Required(List[int], nullable=True)
    effects: List[EffectMessageModel] = Required(List[EffectMessageModel], nullable=True)
    price: float = Required(float)
    isPassiveEquipment: bool = Required(bool)
    possibleAssetCategories: List[int] = Required(List[int], nullable=True)
    possibleAssetIds: List[int] = Required(List[int], nullable=True)
    isSingleUse: bool = Required(bool)
    possible_actions: List[str] = Required(List[str], nullable=True)


@dataclass()
class EquipmentMessageModel():
    id: int = Required(int)
    # TODO: check up with Thomas
    template_id: str = Optional(str)
    type: str = Required(str)
    name: str = Required(str)
    short_description: str = Required(str)
    long_description: str = Required(str)
    impact: List[int] = Required(List[int], nullable=True)
    effects: List[EffectMessageModel] = Required(List[EffectMessageModel], nullable=True)
    price: float = Required(float)
    active: bool = Optional(bool, nullable=True)
    equipt_on_action: int = Required(int, nullable=True)
    equipt_on_asset: int = Required(int, nullable=True)
    isPassiveEquipment: bool = Required(bool)
    possibleAssetCategories: List[int] = Required(List[int], nullable=True)
    possibleAssetIds: List[int] = Required(List[int], nullable=True)
    isSingleUse: bool = Required(bool)
    possible_actions: List[str] = Required(List[str], nullable=True)
    used_on_action: int = Required(int, nullable=True)
    used_on_asset: int = Required(int, nullable=True)
    owner: int = Required(int, nullable=True)
    isUsed: bool = Required(bool, nullable=True)
    isReusable: bool = Required(bool, nullable=True)
    isAttackEquipment: bool = Required(bool, nullable=True)
    isDefenseEquipment: bool = Required(bool, nullable=True)
    
    
@dataclass()
class ActionTemplateMessageModel():
    id: str = Required(str)
    name: str = Required(str)
    short_description: str = Required(str)
    long_description: str = Required(str)
    effects: List[EffectMessageModel] = Required(List[EffectMessageModel])
    impact: List[int] = Required(List[int])
    soph_requirement: int = Required(int)
    requiresAdmin: bool = Required(bool)
    requiredEquipment: List[EquipmentTemplateMessageModel] = Required(List[EquipmentTemplateMessageModel])
    asset_categories: List[int] = Required(List[int])
    attack_stage: int = Required(int)
    oses: List[int] = Required(List[int])
    card_type: int = Required(int)
    actor_type: int = Required(int)
    actionPointCost: int = Required(int)
    success_chance: float = Optional(float, nullable=True)
    detection_chance: float = Optional(float, nullable=True)
    detection_chance_failed: float = Optional(float, nullable=True)
    target_type: int = Optional(int, nullable=True)
    predefined_attack_mask: str = Optional(str, nullable=True)
    requires_attack_mask: bool = Optional(bool, nullable=True)
    def_type: int = Optional(int, nullable=True)    
    possible_actions: List[str] = Optional(List[str], nullable=True)
    affectedAttackActions: List[str] = Optional(List[str], nullable=True)
    affectedDefenseActions: List[str] = Optional(List[str], nullable=True)


@dataclass()
class ActionMessageModel():
    id: int = Required(int)
    template_id: str = Required(str)
    name: str = Required(str)
    short_description: str = Required(str)
    long_description: str = Required(str)
    effects: List[EffectMessageModel] = Required(List[EffectMessageModel])
    impact: List[int] = Required(List[int])
    soph_requirement: int = Required(int)
    requiresAdmin: bool = Required(bool)
    requiredEquipment: List[EquipmentTemplateMessageModel] = Required(List[EquipmentTemplateMessageModel])
    asset_categories: List[int] = Required(List[int])
    attack_stage: int = Required(int)
    oses: List[int] = Required(List[int])
    card_type: int = Required(int)
    actor_type: int = Required(int)
    actionPointCost: int = Required(int)
    success_chance: float = Optional(float, nullable=True)
    detection_chance: float = Optional(float, nullable=True)
    detection_chance_failed: float = Optional(float, nullable=True)
    target_type: int = Optional(int, nullable=True)
    predefined_attack_mask: str = Optional(str, nullable=True)
    def_type: int = Optional(int, nullable=True)
    possible_actions: List[str] = Optional(List[str], nullable=True)
    affectedAttackActions: List[str] = Optional(List[str], nullable=True)
    affectedDefenseActions: List[str] = Optional(List[str], nullable=True)
    actor: int = Optional(int, nullable=True)
    attack_mask_used: str = Optional(str, nullable=True)
    equipment_played_with: Union[List[int], List[EquipmentMessageModel]] = Optional(Options((List[int], List[EquipmentMessageModel])), nullable=True)
    events: List["ActionEventMessageModel"] = Required(List["ActionEventMessageModel"], nullable=True)
    requires_attack_mask: bool = Optional(bool, nullable=True)
    supported_by: List["ActionMessageModel"] = Optional(List["ActionMessageModel"], nullable=True)
    deflectedDamage: List[int] = Required(List[int], nullable=True)
    isUsed: bool = Required(bool, nullable=True)


@dataclass()
class ActionEventMessageModel():
    #action: Dict[str, ActionMessageModel] = Required(Dict[str, Union[int, str]]),
    turn_detected: int = Required(int)
    succeeded: bool = Required(bool)
    deflected: int = Required(int)
    deflectedBy: List[ActionTemplateMessageModel] = Required(List[ActionTemplateMessageModel])
    deflectedDamage: List[int] = Required(List[int])
    asset: int = Required(int, nullable=True)
    current_asset_damage: List[int] = Optional(List[int], nullable=True)
    applied_dependency_damage: List[int] = Optional(List[int], nullable=True)
    damage_dealt: List[int] = Optional(List[int], nullable=True)
    active_damage: List[int] = Optional(List[int], nullable=True)
    countered: List[int] = Optional(List[int], nullable=True)
    fully_countered: bool = Optional(bool, nullable=True)
    counters: int = Optional(int, nullable=True)
    isCounterable: bool = Required(bool, nullable=True)
    lastTurnToCounter: int = Required(int, nullable=True)
    attackMaskUsed: str = Required(str, nullable=True)

    
@dataclass()
class AssetMessageModel():
    # most nullable parameters are because of the asset object in the goal that
    # is basically empty except for the id. Once this is changed to ID and Name
    # only, these nullables can be removed again.
    id: int = Required(int)
    name: str = Required(str)
    description: str = Required(str, nullable=True)
    initially_exposed: bool = Required(bool, nullable=True)
    category: int = Required(int)
    os: int = Required(int, nullable=True)
    attack_stage: int = Required(int)
    parent_asset: int = Required(int, nullable=True)
    child_assets: List[int] = Required(List[int], nullable=True)
    exposed: List[bool] = Required(List[bool], nullable=True)
    damage: List[int] = Required(List[int], nullable=True)
    attack_vectors: List[int] = Required(List[int], nullable=True)
    dependencies: List[int] = Required(List[int], nullable=True)
    active_exploits: List[EquipmentMessageModel] = Required(List[EquipmentMessageModel])
    permanent_effects: List[EffectMessageModel] = Required(List[EffectMessageModel], nullable=True)
    hasAdminRights: bool = Required(bool)
    hasBeenSeen: bool = Required(bool, nullable=True)
    isOffline: bool = Required(bool)
    played_actions: List[ActionMessageModel] = Required(List[ActionMessageModel], nullable=True)
    shield: bool = Required(bool, nullable=True)
    hasBeenSeen: bool = Required(bool, nullable=True)
    hasAdminRights: bool = Required(bool)
    isOffline: bool = Required(bool)


@dataclass()
class GoalMessageModel():
    type: str = Required(str)
    asset: AssetMessageModel = Optional(AssetMessageModel)
    attack_stage: str = Optional(str, nullable=True)
    credits: float = Optional(float, nullable=True)
    damage: List[int] = Optional(List[int])
    defender: int = Optional(int, nullable=True)
    exposed: List[bool] = Optional(List[bool], nullable=True)
    ins: int = Optional(int, nullable=True)


@dataclass()
class ActorMessageModel():
    id: str = Required(str)
    connection_id: str = Required(str)
    user_id: str = Required(str)
    avatar_id: str = Required(str, nullable=True)
    online: bool = Required(bool)
    name: str = Required(str)
    description: str = Required(str, nullable=True)
    soph: int = Required(int, nullable=True)
    det: int = Required(int, nullable=True)
    wealth: int = Required(int, nullable=True)
    ins: int = Required(int, nullable=True)
    ini: int = Required(int, nullable=True)
    credits: float = Required(float, nullable=True)
    insight_shield: int = Required(int, nullable=True)
    actions: List[ActionMessageModel] = Required(List[ActionMessageModel], nullable=True)
    equipment: List[EquipmentMessageModel] = Required(List[EquipmentMessageModel], nullable=True)
    visible_assets: List[AssetMessageModel] = Required(List[AssetMessageModel], nullable=True)
    goal_description: str = Required(str, nullable=True)
    mission_description: str = Required(str, nullable=True)
    goals: List[List[GoalMessageModel]] = Required(List[List[GoalMessageModel]], nullable=True)
    assets: List[AssetMessageModel] = Required(List[AssetMessageModel], nullable=True)
    has_been_detected: bool = Required(bool, nullable=True)
    type: int = Required(int)
    action_points: int = Required(int)

    


@dataclass()
class GameMessageModel():
    actions_offered: List[ActionTemplateMessageModel] = Required(List[ActionTemplateMessageModel])
    amount_selection: int = Required(int)
    phase: str = Required(str)
    players: List[PlayerMessageModel] = Required(List[PlayerMessageModel])
    roles: Dict[str, ActorMessageModel] = Required(Dict[str, ActorMessageModel])
    scenarioDescription: str = Required(str)
    scenarioName: str = Required(str)
    scenario_id: str = Required(str)
    shop: List[EquipmentMessageModel] = Required(List[EquipmentTemplateMessageModel])
    turn: int = Required(int)


@dataclass()
class ErrorsMessageModel():
    error_id: Union[int, List[int]] = Required(Options((int, List[int])))
    error_message: List[str] = Required(Options((str, List[str])))
    multiple_errors: bool = Required(bool)


@dataclass()
class ActionChanceModifierMessageModel():
    bonus: float = Required(float)
    reason: int = Required(int)


@dataclass()
class AssetChangesMessageModel():
    hidden: List[int] = Required(List[int])
    revealed: List[AssetMessageModel] = Required(List[AssetMessageModel])


@dataclass
class PostGameSummaryMessageModel():
    endState: int = Required(int)
    turnsPlayed: int = Required(int)
    attackerUndetectedTurns: int = Required(int, nullable=True)
    actionsDetected: int = Required(int)
    damageDealt: int = Required(int)
    damageHealed: int = Required(int)
    equipmentPurchased: int = Required(int)
    creditsSpent: float = Required(float)
    actionsSucceeded: int = Required(int)
    creditsSpentTotal: float = Required(float)


@dataclass()
class PlayableMessageModel():
    playable: bool = Required(bool)
    success_chance: float = Required(float)
    detection_chance: float = Required(float)
    errors: List[str] = Optional(List[str], nullable=True)
    possible_response_target_ids: Dict[int, List[int]] = Required(Dict[int, List[int]], nullable=True)
    possible_targets: List[int] = Required(List[int], nullable=True)
    action_id: int = Required(int)
    support_action_ids: List[int] = Required(List[int])
    equipment_ids: List[int] = Required(List[int])


@dataclass
class EventEntryMessageModel():
    id: int = Required(int)
    created: str = Required(str)
    type: int = Required(int)


@dataclass
class SelectedActionMessageModel():
    id: str = Required(str)
    amount: int = Required(int)