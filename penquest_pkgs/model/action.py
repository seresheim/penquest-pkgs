from dataclasses import dataclass
from typing import List, Union

from penquest_pkgs.model.effect import Effect
from penquest_pkgs.model.action_event import ActionEvent
from penquest_pkgs.model.equipment_template import EquipmentTemplate
from penquest_pkgs.model.equipment import Equipment


@dataclass()
class Action():
    id :int
    template_id :str
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

    success_chance :float = None
    detection_chance :float = None
    detection_chance_failed :float = None
    target_type :str = None
    predefined_attack_mask :str = None

    transfer_effects :List[Effect] = None

    def_type :int = None    

    actor :int = None
    attack_mask_used :str = None
    equipment_played_with :Union[List[int], List[Equipment]] = None
    events :List[ActionEvent] = None
    possible_actions :List[str] = None
    requires_attack_mask :bool = None
    supported_by :List["Action"] = None
    deflectedDamage :List[int] = None

    def __eq__(self, other):
        if not isinstance(other, Action):
            return False
        return self.id == other.id
    
    def __str__(self):
        return f"{self.name}({self.template_id}|{self.id})"
    
    def __repr__(self):
        return f"{self.name}({self.template_id}|{self.id})"