from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set

from penquest_pkgs.model.validated_action import ValidatedActionModel
from penquest_pkgs.model import ActionModel, EquipmentModel, AssetModel

@dataclass()
class ValidatedPlayActionModel(ValidatedActionModel):
    support_actions: List[ActionModel] = field(default_factory=lambda:[])
    equipment: List[EquipmentModel] = field(default_factory=lambda:[])
    attack_mask: Optional[str] = None
    possible_targets: Optional[Set[AssetModel]] = field(default_factory=lambda:set())
    possible_response_targets: Optional[Dict[int, List[ActionModel]]] = field(default_factory=lambda:dict())
    success_chance: Optional[float] = None
    detection_chance: Optional[float] = None
    
    def get_total_action_point_costs(self) -> int:
        """Returns the total action point cost of the action and all support 
        actions

        Returns:
            int: amount of action points the combination of actions costs
        """
        return sum([a.action_point_cost for a in self.support_actions]) + self.action.action_point_cost
