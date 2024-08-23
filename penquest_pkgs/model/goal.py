from dataclasses import dataclass
from typing import List

from penquest_pkgs.model.asset import Asset  

@dataclass()
class Goal():
    type :str
    asset :Asset
    damage :List[int]
    attack_stage :str = None
    credits :float = None
    defender :int = None
    exposed :List[bool] = None
    ins :int = None