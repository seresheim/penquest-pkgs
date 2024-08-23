
from dataclasses import dataclass
from typing import List

from penquest_pkgs.model.action import Action
from penquest_pkgs.model.asset import Asset
from penquest_pkgs.model.equipment import Equipment
from penquest_pkgs.model.goal import Goal


@dataclass()
class Actor():
    id: str
    type :str
    name :str
    description :str = None
    soph :int = None
    det :int = None
    wealth :int = None
    ini :int = None
    ins :int = None
    credits :float = None
    online :bool = None
    user_id :str = None
    connection_id :str = None
    avatar_id :str = None
    visible_assets :List[Asset] = None
    mission_description :str = None
    goal_descriptions :List[str] = None
    actions :List[Action] = None
    goals :List[Goal] = None
    assets :List[Asset] = None
    equipment :List[Equipment] = None
    hasBeenDetected :bool = None
    insightShield: int = 0

    def __eq__(self, other):
        if not isinstance(other, Actor):
            return False
        return self.id == other.id