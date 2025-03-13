from dataclasses import dataclass
from typing import List

from penquest_pkgs.model import DamageModel, AssetModel
from penquest_pkgs.constants import GoalType

@dataclass()
class GoalModel():
    type: int
    asset: AssetModel
    damage: DamageModel
    attack_stage: str = None
    credits: float = None
    defender: int = None
    exposed: List[bool] = None
    ins: int = None

    def is_asset_goal(self) -> bool:
        return self.type == GoalType.ASSET_GOAL
    
    def is_actor_goal(self) -> bool:
        return self.type == GoalType.ACTOR_GOAL
