from dataclasses import dataclass, field
from typing import Dict

from penquest_pkgs.model.game_option_modes import (
    ActionSuccessMode, 
    ActionDetectionMode, 
    ActionShopMode,
    EquipmentShopMode, 
    SupportActionsMode, 
    InitialAssetStage,
    InitActionsMode,
    ManualDefType,
    MultiTargetSuccess,
    DefenderActionsDetectable,
    DefenderAvailibilityPenalty
)

MODE_ACT_SUCC = "action_success_mode"
MODE_ACT_DET  = "action_detection_mode"
MODE_EQ_SHOP = "equipment_shop_mode"
MODE_ACT_SHOP = "action_shop_mode"
MODE_SUP_ACT = "support_actions_mode"
MODE_OBJ = "game_objectives_mode"
MODE_INIT_ASST_STGE = "initial_asset_stage"
MODE_INIT_ACTS = "initial_action_mode"
MODE_MAN_DEF_TYPE = "manual_def_type_mode"
MODE_INFT_SHIELDS = "infiniteShields"
MODE_MLTI_TGT_SUCC = "multiTargetSuccess"
MODE_DFD_ACTS_DET = "defenderActionsDetectable"
MODE_A_PENALTY = "availabilityPenalty"

@dataclass
class GameOptions:
    """ Sets options for a game to play

    :action_success_mode: determines whether actions have their usual 
        success chance or are always successful.

          Possible values: 
            * 0 ... default, 
            * 1 ... 100% success chance

    :action_detection_mode: determines whether actions have their usual 
        detection chance or are always detected.

          Possible values:
            - 0 ... default
            - 1 ... 100% detection chance

    :equipment_shop_mode: sets which version of equipment shopping is used
        in the game.

          Possible values:
             - 0 ... default (subset can be shopped),
             - 1 ... equipment shopping disabled,
             - 2 ... all equipment available (not only a subset)

    :action_shop_mode: defines how many actions can be drawn

          Possible values:
             - 0 ... default (a random subset),
             - 1 ... all actions offered (not only a subset)

    :support_actions_disabled: defines whether or not support actions are
        part of the game

          Possible values:
             - 0 ... default(no)
             - 1 ... support actions disabled

    :initial_asset_stage: defines the initial stage of all assets in the
        game.

          Possible values:
             - 0 ... default
             - 1 ... initial access
             - 2 ... execution
             - 3 ... random
             
    :manual_def_type_mode: defines the defense type of all actions manually

          Possible values:
             - 0 ... disabled
             - 1 ... prevention
             - 2 ... detection
             - 3 ... response

    :infinite_shield_mode (bool): defines whether shields last infinite or not

          Possible values:
             - False/0 ... disabled
             - True/1 ... enabled

    :multi_target_success_mode: defines whether for multi target actions
        the success is rolled out for each target individually or once for all

          Possible values:
             - 0 ... one roll per target
             - 1 ... one roll for all attacker targets
             - 2 ... one roll for all defender targets
             - 3 ... one roll for all targets

    :defender_actions_detectable_mode: makes the defender's actions visible
        for the attacker. 

          Possible values:
             - 0 ... response only
             - 1 ... prevention and response
             - 2 ... detection and response
             - 3 ... All 

    :defender_availablility_penalty_mode: penalizes the defender for having
        assets with A - 3 damage. 

          Possible values:
             - 0 ... enabled,
             - 1 ... disabled
            
    """

    @staticmethod
    def from_dict(dict: Dict[str, int]):
        return GameOptions(
            action_success_mode=ActionSuccessMode(dict.get(MODE_ACT_SUCC, 0)),
            action_detection_mode=ActionDetectionMode(
                dict.get(MODE_ACT_DET, 0)
            ),
            equipment_shop_mode=EquipmentShopMode(dict.get(MODE_EQ_SHOP, 0)),
            action_shop_mode=ActionShopMode(dict.get(MODE_ACT_SHOP, 0)),
            support_actions_mode=SupportActionsMode(dict.get(MODE_SUP_ACT, 0)),
            initial_asset_stage=InitialAssetStage(
                dict.get(MODE_INIT_ASST_STGE, 0)
            ),
            initial_action_mode=InitActionsMode(dict.get(MODE_INIT_ACTS, 0)),
            manual_def_type_mode=ManualDefType(dict.get(MODE_MAN_DEF_TYPE, 0)),
            infinite_shield_mode=bool(dict.get(MODE_INFT_SHIELDS, 0)),
            multi_target_success_mode=MultiTargetSuccess(
                dict.get(MODE_MLTI_TGT_SUCC, 0)
            ),
            defender_actions_detectable_mode=DefenderActionsDetectable(
                dict.get(MODE_DFD_ACTS_DET, 0)
            ),
            defender_availablility_penalty_mode=DefenderAvailibilityPenalty(
                dict.get(MODE_A_PENALTY, 0)
            )
        )

    action_success_mode: ActionSuccessMode = field(
        default=ActionSuccessMode.DEFAULT
    )
    action_detection_mode: ActionDetectionMode = field(
        default=ActionDetectionMode.DEFAULT
    )
    equipment_shop_mode: EquipmentShopMode = field(
        default=EquipmentShopMode.RANDOM
    )
    action_shop_mode: ActionShopMode = field(default=ActionShopMode.RANDOM)
    support_actions_mode: SupportActionsMode = field(
        default=SupportActionsMode.ENABLED
    )
    initial_asset_stage: InitialAssetStage = field(
        default=InitialAssetStage.DEFAULT
    )
    initial_action_mode: InitActionsMode = field(
        default=InitActionsMode.PLAYABLE
    )
    manual_def_type_mode: ManualDefType = field(default=ManualDefType.DISABLED)
    infinite_shield_mode: bool = field(default=False)
    multi_target_success_mode: MultiTargetSuccess = field(
        default=MultiTargetSuccess.ONE_PER_TARGET
    )
    defender_actions_detectable_mode: DefenderActionsDetectable = field(
        default=DefenderActionsDetectable.RESPONSE_ONLY 
    )
    defender_availablility_penalty_mode: DefenderAvailibilityPenalty = field(
        default=DefenderAvailibilityPenalty.ENABLED
    )


    def to_dict(self) -> Dict[str, int]:
        return {
            MODE_ACT_SUCC: self.action_success_mode.value,
            MODE_ACT_DET: self.action_detection_mode.value,
            MODE_EQ_SHOP: self.equipment_shop_mode.value,
            MODE_ACT_SHOP: self.action_shop_mode.value,
            MODE_SUP_ACT: self.support_actions_mode.value,
            MODE_INIT_ASST_STGE: self.initial_asset_stage.value,
            MODE_INIT_ACTS: self.initial_action_mode.value,
            MODE_MAN_DEF_TYPE: self.manual_def_type_mode.value,
            MODE_INFT_SHIELDS: self.infinite_shield_mode,
            MODE_MLTI_TGT_SUCC: self.multi_target_success_mode.value,
            MODE_DFD_ACTS_DET: self.defender_actions_detectable_mode.value,
            MODE_A_PENALTY: self.defender_availablility_penalty_mode.value
        }


