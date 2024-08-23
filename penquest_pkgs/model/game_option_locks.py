from dataclasses import dataclass

@dataclass
class GameOptionLocks():
    action_detection_mode :bool
    action_shop_mode :bool
    action_success_mode :bool
    initial_action_mode :bool
    initial_asset_stage :bool
    manual_def_type_mode :bool
    support_actions_mode :bool
    equipment_shop_mode :bool
    infiniteShields :bool
    multiTargetSuccess :bool
    defenderActionsDetectable :bool
    availabilityPenalty :bool
