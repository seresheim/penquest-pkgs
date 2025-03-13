from dataclasses import dataclass

@dataclass
class GameOptionLocksModel():
    action_success_mode: bool = False
    action_detection_mode: bool = False
    equipment_shop_mode: bool = False
    support_actions_mode: bool = False
    initial_asset_stage: bool = False
    initial_action_mode: bool = False
    manual_def_type_mode: bool = False
    infinite_shields: bool = False
    multi_target_success: bool = False
    defender_actions_detectable: bool = False
    availability_penalty: bool = False
    defender_pre_setup_mode: bool = False
