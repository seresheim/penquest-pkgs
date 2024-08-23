from dataclasses import dataclass
from typing import List


@dataclass()
class Effect():
    id :int
    type :str
    name :str
    description :str
    isPermanent :bool
    effectType :int
    owner_id :int = None
    scope :str = None
    active :bool = None
    attributes :List[str] = None
    equipment :List["EquipmentTemplate"] = None
    num_effects :int = None
    probability :float = None
    turns :int = None
    value :float = None
    
    def __eq__(self, other):
        if not isinstance(other, Effect):
            return False
        return self.id == other.id