from dataclasses import dataclass
from typing import List


@dataclass()
class ActionEvent():
    turn_detected :int
    succeeded :bool
    deflected :int
    deflectedBy :List["ActionTemplate"]
    deflectedDamage :List[int]
    asset :int = None
    current_asset_damage :List[int] = None
    applied_dependency_damage :List[int] = None
    damage_dealt :List[int] = None
    active_damage :List[int] = None
    countered :List[int] = None
    fully_countered :bool = None
    counters :int = None
    isCounterable :bool = None
    lastTurnToCounter :int = None