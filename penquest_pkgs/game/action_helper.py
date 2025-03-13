from typing import List, Dict, Tuple
import itertools

from penquest_pkgs.model import (
    ActionModel,
    AssetModel,
    ActionEventModel,
    ValidatedPlayActionModel
)
from penquest_pkgs.constants import AssetCategory, OS, AttackStage

class ActionHelper():

    @staticmethod
    def get_possible_targets_support_action(
            support_action: ActionModel,
            asset_properties: Dict[Tuple[int, int, int, bool], List[AssetModel]]
        ) -> List[AssetModel]:
        if len(support_action.asset_categories) == 0:
            relevant_asset_cats = AssetCategory.get_all_categories()
        else:
            relevant_asset_cats = support_action.asset_categories

        if len(support_action.oses) == 0:
            relevant_oses = OS.get_all_oses()
        else:
            relevant_oses = support_action.oses

        all_atk_stages = AttackStage.get_all_stages()
        min_atk_stage_idx = all_atk_stages.index(support_action.attack_stage)
        relevant_atk_stages = all_atk_stages[min_atk_stage_idx:]
        
        possible_asset_props = set(itertools.product(
            relevant_asset_cats,
            relevant_oses,
            relevant_atk_stages,
            [support_action.requires_admin]
        ))
        actual_asset_pros = set(asset_properties.keys())
        relevant_asset_props = possible_asset_props.intersection(actual_asset_pros)

        possible_targets = list(itertools.chain.from_iterable(
            asset_properties[prop] for prop in relevant_asset_props
        ))
        return possible_targets

    @staticmethod
    def get_possible_targets(
            validated_action: ValidatedPlayActionModel,
            asset_properties: Dict[Tuple[int, int, int, bool], List[AssetModel]]
        ) -> List[AssetModel]:
        """Retrieves a list of possible target assets for a provided main action
        onto which the main action was (theoretically) playable according to
        asset category, os, attack stage and admin access.

        Args:
            validated_action (ValidatedPlayActionModel): main action a list of possible targets
                is interesting for
            asset_properties (Dict[Tuple[int, int, int, bool], List[AssetModel]]):
                mapping of appearing attributes tuple to list of assets on which
                they appear.

        Returns:
            List[AssetModel]: list of possible targets for the main action
        """
        possible_targets = []

        main_action = validated_action.action
        if len(main_action.asset_categories) == 0:
            relevant_asset_cats = AssetCategory.get_all_categories()
        else:
            relevant_asset_cats = main_action.asset_categories

        if len(main_action.oses) == 0:
            relevant_oses = OS.get_all_oses()
        else:
            relevant_oses = main_action.oses

        all_atk_stages = AttackStage.get_all_stages()
        min_atk_stage_idx = all_atk_stages.index(main_action.attack_stage)
        relevant_atk_stages = all_atk_stages[min_atk_stage_idx:]
        
        possible_asset_props = set(itertools.product(
            relevant_asset_cats,
            relevant_oses,
            relevant_atk_stages,
            [main_action.requires_admin]
        ))
        actual_asset_pros = set(asset_properties.keys())
        relevant_asset_props = possible_asset_props.intersection(actual_asset_pros)
        

        if len(validated_action.equipment) > 0:
            relevant_asset_props = set(
                (cat, os, atk_stage, admin)
                for cat, os, atk_stage, admin in relevant_asset_props
                if any(cat in eq.possible_asset_categories for eq in validated_action.equipment)
            )

        possible_targets = list(itertools.chain.from_iterable(
            asset_properties[prop] for prop in relevant_asset_props
        ))
        return possible_targets

    @staticmethod
    def get_event(action: ActionModel, asset_id: int) -> ActionEventModel:
        """Retrieves the event of an action that is related to a specific asset.

        Args:
            action (ActionModel): action to retrieve the event from
            asset_id (int): asset id to retrieve the event for

        Returns:
            ActionEventModel: event of the action related to the asset
        """
        for event in action.events:
            if event.asset_id == asset_id:
                return event
        return None
