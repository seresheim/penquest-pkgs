from dataclasses import dataclass
from typing import List

from penquest_pkgs.model.effect import EffectModel
from penquest_pkgs.model.damage import DamageModel


@dataclass()
class EquipmentTemplateModel():
    id: str
    type: str
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