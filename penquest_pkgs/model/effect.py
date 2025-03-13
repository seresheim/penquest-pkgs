from dataclasses import dataclass
from typing import List

from penquest_pkgs.constants import EffectType


@dataclass()
class EffectModel():
    id: int
    type: EffectType
    name: str
    description: str
    is_permanent: bool
    owner_id: int = None
    scope: str = None
    active: bool = None
    attributes: List[str] = None
    equipment: List["EquipmentTemplateModel"] = None
    num_effects: int = None
    probability: float = None
    turns: int = None
    value: float = None
    
    def __eq__(self, other):
        if not isinstance(other, EffectModel):
            return False
        return self.id == other.id
    
    def is_inc_dec_effect(self):
        return self.type in [EffectType.MODIFY_ACTION, EffectType.MODIFY_ACTOR]
    
    def is_discovery(self):
        return self.type == EffectType.REVEAL_ASSET