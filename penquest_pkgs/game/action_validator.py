from typing import List, Callable
from enum import Enum

from penquest_pkgs.model import (
    ActionModel,
    ActorModel,
    AssetModel,
    EquipmentModel,
    ValidatedActionModel,
    ValidatedPlayActionModel
)
from penquest_pkgs.game import Game


class ActionValidationTags(Enum):
    pass


class ActionValidationBase():

    def __init__(self, validator: Callable, *tags: ActionValidationTags):
        self.validate = validator
        self.tags = set(tags)

    def has_tag(self, tag) -> bool:
        return tag in self.tags


class CommonValidation(ActionValidationBase):

    def __init__(self, validator: Callable[[Game, ActorModel, ValidatedActionModel], None], *tags):
        super(CommonValidation, self).__init__(validator, *tags)


class AssetValidation(ActionValidationBase):

    def __init__(self, validator: Callable[[Game, ActorModel, AssetModel, ValidatedActionModel], None], *tags):
        super(AssetValidation, self).__init__(validator, *tags)


class EquipmentValidation(ActionValidationBase):

    def __init__(self, validator: Callable[[Game, ActorModel, EquipmentModel, ValidatedActionModel], None], *tags):
        super(EquipmentValidation, self).__init__(validator, *tags)


class ActionValidation(ActionValidationBase):

    def __init__(self, validator: Callable[[Game, ActorModel, AssetModel, ActionModel, ValidatedActionModel], None], *tags):
        super(ActionValidation, self).__init__(validator, *tags)


class EqiupmentAssetValidation(ActionValidationBase):

    def __init__(self, validator: Callable[[Game, ActorModel, EquipmentModel, AssetModel, ValidatedActionModel], None], *tags):
        super(EqiupmentAssetValidation, self).__init__(validator, *tags)


class ActionValidatorOptions():

    def __init__(self):
        self.stop_on_error: bool = False
        self.skip_asset_checks: bool = False
        self.bot_run: bool = False


class ActionValidator():

    def __init__(self):
        self.common_validators: List[CommonValidation] = []
        self.asset_validators: List[AssetValidation] = []
        self.equipment_validators: List[EquipmentValidation] = []
        self.action_validators: List[ActionValidation] = []
        self.equipment_asset_validators: List[EqiupmentAssetValidation] = []

    def add_validation(self, validator, *tags: ActionValidationTags):
        self.common_validators.append(CommonValidation(validator, *tags))

    def add_asset_validation(self, validator, *tags: ActionValidationTags):
        self.asset_validators.append(AssetValidation(validator, *tags))

    def add_equipment_validation(self, validator, *tags: ActionValidationTags):
        self.equipment_validators.append(EquipmentValidation(validator, *tags))
    
    def add_action_validation(self, validator, *tags: ActionValidationTags):
        self.action_validators.append(ActionValidation(validator, *tags))

    def add_equipment_asset_validation(self, validator, *tags: ActionValidationTags):
        self.equipment_asset_validators.append(EqiupmentAssetValidation(validator, *tags))

    def is_rule_valid(self, validation: Callable, validated_action: ValidatedActionModel) -> bool:
        errors_before = len(validated_action.errors)
        validation()
        return len(validated_action.errors) == errors_before

    def validate(
            self,
            game: Game,
            actor: ActorModel,
            validated_action: ValidatedActionModel,
            config: Callable[[ActionValidatorOptions], None] = None
        ):
        options = ActionValidatorOptions()
        if config is not None:
            config(options)

        for rule in self.common_validators:
            if self.is_rule_valid(lambda: rule.validate(game, actor, validated_action), validated_action):
                continue
            if options.stop_on_error:
                return
            
        # exit if the action is not a play action, otherwise perform play
        # action checks for the other fields.
        if not isinstance(validated_action, ValidatedPlayActionModel):
            return
        
        # perform all checks for each equipment
        for equipment in validated_action.equipment:
            for rule in self.equipment_validators:
                if self.is_rule_valid(lambda: rule.validate(game, actor, equipment, validated_action), validated_action):
                    continue
                if options.stop_on_error:
                    return
        
        if not options.skip_asset_checks:
            for asset in validated_action.possible_targets:
                # main action checks
                for rule in self.action_validators:
                    if self.is_rule_valid(lambda: rule.validate(game, actor, asset, validated_action.main_action, validated_action), validated_action):
                        continue
                    if options.stop_on_error:
                        return
                
                # support action checks
                for support_action in validated_action.support_actions:
                    for rule in self.action_validators:
                        if self.is_rule_valid(lambda: rule.validate(game, actor, asset, support_action, validated_action), validated_action):
                            continue
                        if options.stop_on_error:
                            return
                        
                # equipment checks
                for equipment in validated_action.equipment:
                    for rule in self.equipment_asset_validators:
                        if self.is_rule_valid(lambda: rule.validate(game, actor, equipment, asset, validated_action), validated_action):
                            continue
                        if options.stop_on_error:
                            return

                # asset checks
                for rule in self.asset_validators:
                    if self.is_rule_valid(lambda: rule.validate(game, actor, asset, validated_action), validated_action):
                        continue
                    if options.stop_on_error:
                        return
