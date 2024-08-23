
from dataclasses import dataclass
from typing import List

from penquest_pkgs.model.effect import Effect
from penquest_pkgs.model.equipment_template import EquipmentTemplate
from penquest_pkgs.model.action import Action

@dataclass()
class ActionTemplate():
    id :str
    name :str
    short_description :str
    long_description :str
    effects :List[Effect]
    impact :List[int]
    soph_requirement :int
    requiresAdmin :bool
    requiredEquipment :List[EquipmentTemplate]
    asset_categories :List[int]
    attack_stage :int
    oses :List[int]
    card_type :str
    actor_type :str
    transfer_effects :List[Effect] = None
    success_chance :float = None
    detection_chance :float = None
    detection_chance_failed :float = None
    target_type :str = None
    predefined_attack_mask :str = None
    requires_attack_mask :bool = None
    def_type :int = None    
    possible_actions :List[str] = None
    

    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return self.id == other.id
    
    def __str__(self):
        return f"{self.name}({self.id})"
    
    def __repr__(self):
        return f"{self.name}({self.id})"