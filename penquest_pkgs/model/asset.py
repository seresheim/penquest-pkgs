from dataclasses import dataclass
from typing import List

from penquest_pkgs.model import (
    DamageModel,
    EffectModel,
    EquipmentModel,
    ActionModel,
    ExposedModel
)


@dataclass()
class AssetModel():
    # most nullable parameters are because of the asset object in the goal that
    # is basically empty except for the id. Once this is changed to ID and Name
    # only, these nullables can be removed again.
    id: int
    name: str
    category: int
    attack_stage: int
    active_exploits: List[EquipmentModel]
    has_admin_rights: bool
    is_offline: bool
    description: str = None
    initially_exposed: bool = None
    os: int = None
    parent_asset: int = None
    child_assets: List[int] = None
    exposed: ExposedModel = None
    damage: DamageModel = None
    attack_vectors: List[int] = None
    dependencies: List[int] = None
    permanent_effects: List[EffectModel] = None
    played_actions: List[ActionModel] = None
    shield: bool = None
    has_been_seen: bool = None

    def __eq__(self, other):
        if not isinstance(other, AssetModel):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)
    
    def is_attack_vector_partially_available(self, attack_mask: str):
        return any([self.exposed.is_exposed(c) for c in attack_mask])
    
    def is_damaged(self):
        return any(self.damage[i] > 0 for i in range(len(self.damage)))