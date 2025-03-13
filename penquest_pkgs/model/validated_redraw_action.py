from dataclasses import dataclass

from penquest_pkgs.exceptions import Errors
from penquest_pkgs.model.validated_action import ValidatedActionModel
from penquest_pkgs.model.action_template import ActionTemplateModel

@dataclass()
class ValidatedRedrawActionModel(ValidatedActionModel):
    action: ActionTemplateModel

    def get_total_action_point_costs(self) -> int:
        """Returns the total action point cost of the action and all support 
        actions

        Returns:
            int: amount of action points the combination of actions costs
        """
        return self.action.action_point_cost

    def is_missing_action_points(self) -> bool:
        """Indicates whether the action is not playable because of insufficient
        action points.

        Returns:
            bool: indicates if the action is not playable because of insufficient
                action points
        """
        for exception in self.errors:
            if exception.error_type == Errors.InsufficientActionPointsError:
                return True
        return False

    def is_missing_credits(self) -> bool:
        """Indicates whether the action is not playable because of insufficient
        credits.

        Returns:
            bool: indicates if the action is not playable because of insufficient
                credits
        """
        for exception in self.errors:
            if exception.error_type == Errors.NotEnoughCreditsError:
                return True
        return False

    def is_missing_equipment(self) -> bool:
        """Indicates whether the action is not playable because of missing
        retuired equipment.

        Returns:
            bool: indicates if the action is not playable because of missing
                required equipment
        """
        for exception in self.errors:
            if exception.error_type == Errors.ActionRequiredEquipmentMissing:
                return True
        return False

    def is_missing_target_asset(self) -> bool:
        """Indicates whether the action is not playable because of missing
        compatible target assets.

        Returns:
            bool: indicates if the action is not playable because of missing
                compatible target assets
        """
        for exception in self.errors:
            if exception.error_type == Errors.MissingAssetError:
                return True
        return False

    def is_almost_playable(self) -> bool:
        """Indicates whether the action is almost playable, but not only missing
        some required equipment.

        Returns:
            bool: indicates if the action is almost playable, but not yet
        """
        return all([exception.code == Errors.ActionRequiredEquipmentMissing for exception in self.errors])