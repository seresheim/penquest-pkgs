from typing import Union

from penquest_pkgs.model import (
    GoalModel,
    AssetModel,
    ActionModel,
    ActionTemplateModel
)

class AssetHelper():

    @staticmethod
    def is_asset_goal_achieved(goal : GoalModel, asset: AssetModel) -> bool:
        """Indicates whether an asset goal for a specific asset is achieved

        Args:
            goal (GoalModel): the asset goal in question that may be achieved
            asset (AssetModel): the target of the asset goal

        Returns:
            bool: indicates whether the asset goal is achieved
        """
        # if it is not an asset goal, then the goal is not achieved
        if not goal.is_asset_goal():
            return False

        # if the wrogn target asset is provided then the goal is not achieved
        if goal.asset.id != asset.id:
            return False

        # check exposedness, attack stage and damage of the asset
        exposed_achieved = all(
            goal.exposed[i] <= asset.exposed[i]
            for i in range(len(goal.exposed))
        )
        attack_stage_achieved = goal.attack_stage <= asset.attack_stage
        damage_achieved = goal.damage <= asset.damage

        return exposed_achieved and attack_stage_achieved and damage_achieved

    @staticmethod
    def is_action_playable_on_asset(
            action: Union[ActionModel, ActionTemplateModel],
            asset: AssetModel
        ) -> bool:
        """Indicates whether an action can be played on a specific asset"
        """
        if asset.is_offline:
            return False
        if asset.os not in action.oses:
            return False
        if asset.category not in action.asset_categories:
            return False
        if asset.attack_stage < action.attack_stage:
            return False
        if action.requires_admin and not asset.has_admin_rights:
            return False
        return True
