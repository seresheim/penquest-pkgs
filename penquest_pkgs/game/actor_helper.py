from typing import List, Dict, Tuple

from penquest_pkgs.constants import (
    AttackStage,
    MIN_ACTION_POINTS,
    ActorType,
)
from penquest_pkgs.model import (
     ActorModel,
     AssetModel
)

class ActorHelper():

    @staticmethod
    def get_min_aps(actor: ActorModel) -> int:
        """Returns the minimum amount of action points the agent has

        :return: minimum amount of action points
        """
        # the check on ini must be 1 instead of 0, because the event that sends
        # the action point with 0 is processed after the check below is executed
        if actor.type == ActorType.ATTACK and actor.ini <= 1:
            return 0
        return MIN_ACTION_POINTS

    @staticmethod
    def get_visible_asset_properties(
            assets: List[AssetModel]
        ) -> Dict[Tuple[int, int, int, bool], List[AssetModel]]:
        """Creates a dictionary with all combinations of asset category, os,
        attack stage and admin access as they appear on assets on the game
        board. Keys are tuple of the appearing combinations and values are 
        lists of assets.

        Args:
            game_state (GameStateModel): state of the game
            actor (ActorModel): actor object of the client

        Returns:
            Dict[Tuple[int, int, int, bool], List[AssetModel]]: mapping of
                appearing attributes tuple to list of assets on which they
                appear.
        """
        asset_properties = dict()

        attack_stages = AttackStage.get_all_stages()

        for asset in assets:
            if not asset.is_offline:
                atk_stage = asset.attack_stage if asset.attack_stage > 0 else 1
                max_idx = attack_stages.index(atk_stage)
                relevant_stages = attack_stages[:max_idx + 1]
                for attack_stage in relevant_stages:
                    prop_tuple = (asset.category, asset.os, attack_stage, asset.has_admin_rights)
                    if prop_tuple not in asset_properties:
                        assets = []
                        asset_properties[prop_tuple] = assets
                    else:
                        assets = asset_properties[prop_tuple]
                    assets.append(asset)

        return asset_properties