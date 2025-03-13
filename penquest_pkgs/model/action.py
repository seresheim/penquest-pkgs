from dataclasses import dataclass
from typing import List, Union

from penquest_pkgs.model import (
    DamageModel,
    EffectModel,
    EquipmentTemplateModel,
    EquipmentModel,
    ActionEventModel
)
from penquest_pkgs.constants import ActorType, DefType


@dataclass()
class ActionModel():
    id: int
    template_id: str
    name: str
    short_description: str
    long_description: str
    effects: List[EffectModel]
    impact: DamageModel
    soph_requirement: int
    requires_admin: bool
    required_equipment: List[EquipmentTemplateModel]
    asset_categories: List[int]
    attack_stage: int
    oses: List[int]
    card_type: int
    actor_type: int
    action_point_cost: int
    success_chance: float = None
    detection_chance: float = None
    detection_chance_failed: float = None
    target_type: int = None
    predefined_attack_mask: str = None
    def_type: int = None
    possible_actions: List[str] = None
    affected_attack_actions: List[str] = None
    affected_defense_actions: List[str] = None
    actor_id: int = None
    attack_mask_used: str = None
    equipment_played_with: Union[List[int], List[EquipmentModel]] = None
    events: List[ActionEventModel] = None
    requires_attack_mask: bool = None
    supported_by: List["ActionModel"] = None
    deflected_damage: DamageModel = None
    is_used: bool = None

    def __eq__(self, other):
        if not isinstance(other, ActionModel):
            return False
        return self.id == other.id
    
    def __str__(self):
        return f"{self.name}({self.template_id}|{self.id})"
    
    def __repr__(self):
        return f"{self.name}({self.template_id}|{self.id})"
    
    def has_predefiend_attack_mask(self):
        return self.predefined_attack_mask is not None and self.predefined_attack_mask != ""
    
    def is_attack_action(self):
        return self.actor_type == ActorType.ATTACK
    
    def is_defense_action(self):
        return self.actor_type == ActorType.DEFENCE
    
    def is_prevention_action(self):
        if not self.is_defense_action():
            return False
        return self.def_type == DefType.PREVENTION
    
    def is_detection_action(self):
        if not self.is_defense_action():
            return False
        return self.def_type == DefType.DETECTION
    
    def is_response_action(self):
        if not self.is_defense_action():
            return False
        return self.def_type == DefType.RESPONSE
    
    @property
    def has_heal_part(self):
        return any([i < 0 for i in self.impact])