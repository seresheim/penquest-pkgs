from dataclasses import dataclass
from typing import List

from penquest_pkgs.model.effect import EffectModel
from penquest_pkgs.model.damage import DamageModel

@dataclass()
class EquipmentModel():
    id: int
    # TODO: check up with Thomas
    template_id: str
    type: int
    name: str
    short_description: str
    long_description: str
    price: float
    is_passive_equipment: bool
    possible_asset_categories: List[int]
    possible_asset_ids: List[int]
    is_single_use: bool
    impact: DamageModel = None
    effects: List[EffectModel] = None
    possible_actions: List[str] = None
    active: bool = None
    equipt_on_action: int = None
    equipt_on_asset: int = None
    used_on_action: int = None
    used_on_asset: int = None
    owner_id: int = None
    is_used: bool = None
    is_reusable: bool = None
    is_attack_equipment: bool = None
    is_defense_equipment: bool = None

    def __eq__(self, other):
        if not isinstance(other, EquipmentModel):
            return False
        return self.id == other.id
    
    def __str__(self):
        return f"{self.name}({self.template_id}|{self.id})"
    
    def __repr__(self):
        return f"{self.name}({self.template_id}|{self.id})"
    
    @property
    def is_local_equipment(self) -> bool:
        return not self.is_passive_equipment
    
    def is_compatible_with(self, asset_category: int) -> bool:
        return self.possible_asset_categories is None or asset_category in self.possible_asset_categories
    
    def is_compatible_with_asset_id(self, asset_id: int) -> bool:
        return self.possible_asset_ids is None or asset_id in self.possible_asset_ids
    