from penquest_pkgs.network.ProtocolParts import Required, Optional, Options
from penquest_pkgs.constants.GameEndedState import GameEndedState
from typing import List, Dict
from dataclasses import dataclass


@dataclass()
class Player():
    id = Required(int)
    connection_id = Required(str)
    avatar_id = Required(int, nullable=True)
    name = Required(str)
    online = Required(bool)
    user_id = Required(str)


@dataclass()
class GameOptions():
    action_detection_mode = Required(int)
    action_shop_mode = Required(int)
    action_success_mode = Required(int)
    initial_action_mode = Required(int)
    initial_asset_stage = Required(int)
    manual_def_type_mode = Required(int)
    support_actions_mode = Required(int)
    equipment_shop_mode = Required(int)
    infiniteShields = Required(int)
    multiTargetSuccess = Required(int)
    defenderActionsDetectable = Required(int)
    availabilityPenalty = Required(int)


@dataclass
class GameOptionLocks():
    action_detection_mode = Required(bool)
    action_shop_mode = Required(bool)
    action_success_mode = Required(bool)
    initial_action_mode = Required(bool)
    initial_asset_stage = Required(bool)
    manual_def_type_mode = Required(bool)
    support_actions_mode = Required(bool)
    equipment_shop_mode = Required(bool)
    infiniteShields = Required(bool)
    multiTargetSuccess = Required(bool)
    defenderActionsDetectable = Required(bool)
    availabilityPenalty = Required(bool)


@dataclass()
class SlotInfo():
    slotId = Required(int)
    name = Required(str)
    type = Required(int)
    isReady = Required(bool)


@dataclass()
class ScenarioTeaser():
    id = Required(str)
    name = Required(str)
    description = Required(str)
    availableSlots = Required(List[SlotInfo])


@dataclass
class GoalDesc():
    id = Required(str)
    description = Required(str)
    isDefault = Required(bool)


@dataclass()
class Lobby():
    admin = Required(Player)
    code = Required(str)
    players = Required(Dict[int, Player], nullable=True)
    scenario = Required(ScenarioTeaser, nullable=True)
    game_options = Required(GameOptions)
    gameOptionLocks = Required(GameOptionLocks)
    availableGoals = Required(List[GoalDesc], nullable=True)


@dataclass()
class Effect():
    id = Required(int)
    type = Required(str)
    name = Required(str)
    description = Required(str)
    owner_id = Required(int, nullable=True)
    scope = Required(str, nullable=True)
    active = Optional(bool, nullable=True)
    attributes = Optional(List[str], nullable=True)
    equipment = Optional(List["EquipmentTemplate"], nullable=True)
    num_effects = Optional(int, nullable=True)
    probability = Optional(float, nullable=True)
    turns = Optional(int, nullable=True)
    value = Optional(float, nullable=True)
    isPermanent = Required(bool)
    effectType = Required(int)


@dataclass()
class Equipment():
    id = Required(int)
    # TODO: check up with Thomas
    template_id = Optional(str)
    type = Required(str)
    name = Required(str)
    short_description = Required(str)
    long_description = Required(str)
    impact = Required(List[int], nullable=True)
    effects = Required(List[Effect], nullable=True)
    transfer_effects = Required(List[Effect], nullable=True)
    price = Required(float)
    active = Optional(bool, nullable=True)
    equipt_on_action = Required(int, nullable=True)
    equipt_on_asset = Required(int, nullable=True)
    isPassiveEquipment = Required(bool)
    isSingleUse = Required(bool)
    possible_actions = Required(List[str], nullable=True)
    used_on_action = Required(int, nullable=True)
    used_on_asset = Required(int, nullable=True)
    owner = Required(int, nullable=True)
    

@dataclass()
class EquipmentTemplate():
    id = Required(str)
    type = Required(str)
    name = Required(str)
    short_description = Required(str)
    long_description = Required(str)
    impact = Required(List[int], nullable=True)
    effects = Required(List[Effect], nullable=True)
    transfer_effects = Required(List[Effect], nullable=True)
    price = Required(float)
    isPassiveEquipment = Required(bool)
    isSingleUse = Required(bool)
    possible_actions = Required(List[str], nullable=True)


@dataclass()
class ActionEvent():
    turn_detected = Required(int)
    succeeded = Required(bool)
    deflected = Required(int)
    deflectedBy = Required(List["ActionTemplate"])
    deflectedDamage = Required(List[int])
    asset = Optional(int, nullable=True)
    current_asset_damage = Optional(List[int], nullable=True)
    applied_dependency_damage = Optional(List[int], nullable=True)
    damage_dealt = Optional(List[int], nullable=True)
    active_damage = Optional(List[int], nullable=True)
    countered = Optional(List[int], nullable=True)
    fully_countered = Optional(bool, nullable=True)
    counters = Optional(int, nullable=True)
    isCounterable = Required(bool, nullable=True)
    lastTurnToCounter = Required(int, nullable=True)
    
    
@dataclass()
class ActionTemplate():
    id = Required(str)
    name = Required(str)
    short_description = Required(str)
    long_description = Required(str)
    effects = Required(List[Effect])
    impact = Required(List[int])
    soph_requirement = Required(int)
    requiresAdmin = Required(bool)
    requiredEquipment = Required(List[EquipmentTemplate])
    asset_categories = Required(List[int])
    attack_stage = Required(int)
    oses = Required(List[int])
    card_type = Required(str)
    actor_type = Required(str)

    transfer_effects = Optional(List[Effect], nullable=True)
    success_chance = Optional(float, nullable=True)
    detection_chance = Optional(float, nullable=True)
    detection_chance_failed = Optional(float, nullable=True)
    target_type = Optional(str, nullable=True)
    predefined_attack_mask = Optional(str, nullable=True)
    requires_attack_mask = Optional(bool, nullable=True)
    def_type = Optional(int, nullable=True)    
    possible_actions = Optional(List[str], nullable=True)


@dataclass()
class Action():
    id = Required(int)
    template_id = Required(str)
    name = Required(str)
    short_description = Required(str)
    long_description = Required(str)
    effects = Required(List[Effect])
    impact = Required(List[int])
    soph_requirement = Required(int)
    requiresAdmin = Required(bool)
    requiredEquipment = Required(List[EquipmentTemplate])
    asset_categories = Required(List[int])
    attack_stage = Required(int)
    oses = Required(List[int])
    card_type = Required(str)
    actor_type = Required(str)

    success_chance = Optional(float, nullable=True)
    detection_chance = Optional(float, nullable=True)
    detection_chance_failed = Optional(float, nullable=True)
    target_type = Optional(str, nullable=True)
    predefined_attack_mask = Optional(str, nullable=True)

    transfer_effects = Optional(List[Effect], nullable=True)

    def_type = Optional(int, nullable=True)    

    actor = Optional(int, nullable=True)
    attack_mask_used = Optional(str, nullable=True)
    equipment_played_with = Optional(Options((List[int], List[Equipment])), nullable=True)
    events = Optional(List[ActionEvent], nullable=True)
    possible_actions = Optional(List[str], nullable=True)
    requires_attack_mask = Optional(bool, nullable=True)
    supported_by = Optional(List["Action"], nullable=True)
    deflectedDamage = Required(List[int], nullable=True)

    
@dataclass()
class Asset():
    # most nullable parameters are because of the asset object in the goal that
    # is basically empty except for the id. Once this is changed to ID and Name
    # only, these nullables can be removed again.
    id = Required(int)
    name = Required(str)
    description = Required(str, nullable=True)
    initially_exposed = Required(bool, nullable=True)
    category = Required(int)
    os = Required(int, nullable=True)
    attack_stage = Required(int)
    parent_asset = Required(int, nullable=True)
    child_assets = Required(List[int], nullable=True)
    exposed = Required(List[bool], nullable=True)
    damage = Required(List[int], nullable=True)
    attack_vectors = Required(List[int], nullable=True)
    dependencies = Required(List[int], nullable=True)
    active_exploits = Required(List[Equipment])
    permanent_effects = Required(List[Effect], nullable=True)
    hasAdminRights = Required(bool)
    hasBeenSeen = Required(bool, nullable=True)
    isOffline = Required(bool)
    played_actions = Required(List[Action], nullable=True)
    shield = Required(bool, nullable=True)
    hasBeenSeen = Required(bool, nullable=True)
    hasAdminRights = Required(bool)
    isOffline = Required(bool)


@dataclass()
class Goal():
    type = Required(str)
    asset = Optional(Asset)
    attack_stage = Optional(str, nullable=True)
    credits = Optional(float, nullable=True)
    damage = Optional(List[int])
    defender = Optional(int, nullable=True)
    exposed = Optional(List[bool], nullable=True)
    ins = Optional(int, nullable=True)


@dataclass()
class Actor():
    id = Required(str)
    type = Required(str)
    name = Required(str)
    description = Required(str, nullable=True)
    soph = Required(int, nullable=True)
    det = Required(int, nullable=True)
    wealth = Required(int, nullable=True)
    ini = Required(int, nullable=True)
    ins = Required(int, nullable=True)
    credits = Required(float, nullable=True)
    online = Optional(bool)
    user_id = Optional(str)
    connection_id = Required(str)
    avatar_id = Required(str, nullable=True)
    visible_assets = Required(List[Asset], nullable=True)
    mission_description = Required(str, nullable=True)
    goal_descriptions = Required(List[str], nullable=True)
    actions = Required(List[Action], nullable=True)
    goals = Optional(List[Goal], nullable=True)
    assets = Optional(List[Asset], nullable=True)
    equipment = Required(List[Equipment], nullable=True)
    hasBeenDetected = Required(bool, nullable=True)
    insightShield = Required(int, nullable=True)


@dataclass()
class Game():
    actions_offered = Required(List[ActionTemplate])
    amount_selection = Required(int)
    phase = Required(str)
    players = Required(List[Player])
    roles = Required(Dict[str, Actor])
    scenarioDescription = Required(str)
    scenarioName = Required(str)
    scenario_id = Required(str)
    shop = Required(List[EquipmentTemplate])
    turn = Required(int)


@dataclass()
class Errors():
    error_id = Required(Options((int, List[int])))
    error_message = Required(Options((str, List[str])))
    multiple_errors = Required(bool)


@dataclass()
class ActionChanceModifier():
    bonus = Required(float)
    reason = Required(int)


@dataclass()
class AssetChanges():
    hidden = Required(List[int])
    revealed = Required(List[Asset])


@dataclass
class PostGameSummary():
    endState = Required(GameEndedState)
    turnsPlayed = Required(int)
    attackerUndetectedTurns = Required(int, nullable=True)
    actionsDetected = Required(int)
    damageDealt = Required(int)
    damageHealed = Required(int)
    equipmentPurchased = Required(int)
    creditsSpent = Required(float)
    actionsSucceeded = Required(int)
    creditsSpentTotal = Required(float)


@dataclass()
class Playable():
    playable = Required(bool)
    success_chance = Required(float)
    detection_chance = Required(float)
    errors = Optional(List[str], nullable=True)
    possible_response_target_ids = Required(Dict[int, List[int]], nullable=True)
    possible_targets = Required(List[int], nullable=True)
    action_id = Required(int)
    support_action_ids = Required(List[int])
    equipment_ids = Required(List[int])



@dataclass
class EventEntry():
    id=Required(int)
    created=Required(str)
    type=Required(int)
    #payload=Required()