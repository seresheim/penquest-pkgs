
from dataclasses import dataclass
from typing import List

from penquest_pkgs.constants import ActorType, DefType

from penquest_pkgs.model.effect import EffectModel
from penquest_pkgs.model.equipment_template import EquipmentTemplateModel
from penquest_pkgs.model.damage import DamageModel

@dataclass()
class ActionTemplateModel():
    id: str
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
    target_type: str = None
    predefined_attack_mask: str = None
    requires_attack_mask: bool = None
    def_type: int = None
    possible_actions: List[str] = None
    affected_attack_actions: List[str] = None
    affected_defense_actions: List[str] = None

    def __eq__(self, other):
        if not isinstance(other, ActionTemplateModel):
            return False
        return self.id == other.id

    def __str__(self):
        return f"{self.name}({self.id})"

    def __repr__(self):
        return f"{self.name}({self.id})"

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
