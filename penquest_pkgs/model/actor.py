
from dataclasses import dataclass
from typing import List

from penquest_pkgs.model import (
    EquipmentModel,
    ActionModel,
    AssetModel,
    GoalModel
)

from penquest_pkgs.constants import ActorType


@dataclass()
class ActorModel():
    id: str
    type: int
    name: str
    action_points: int
    connection_id: str = None
    user_id: str = None
    avatar_id: str = None
    online: bool = None
    description: str = None
    soph: int = None
    det: int = None
    wealth: int = None
    ins: int = None
    ini: int = None
    credits: float = None
    insight_shield: int = None
    actions: List[ActionModel] = None
    equipment: List[EquipmentModel] = None
    visible_assets: List[AssetModel] = None
    goal_description: str = None
    mission_description: str = None
    goals: List[List[GoalModel]] = None
    assets: List[AssetModel] = None
    has_been_detected: bool = None
    
    def __eq__(self, other):
        if not isinstance(other, ActorModel):
            return False
        return self.id == other.id

    @property
    def is_attacker(self):
        return self.type == ActorType.ATTACK

    @property
    def is_defender(self):
        return self.type == ActorType.DEFENCE