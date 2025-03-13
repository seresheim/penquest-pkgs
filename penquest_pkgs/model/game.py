from dataclasses import dataclass
from typing import List, Dict

from penquest_pkgs.model import (
    PlayerModel,
    EquipmentTemplateModel,
    ActionTemplateModel,
    ActorModel,
)


@dataclass()
class GameModel():
    actions_offered: List[ActionTemplateModel]
    amount_selection: int
    phase: str
    players: List[PlayerModel]
    roles: Dict[str, ActorModel]
    scenario_description: str
    scenario_name: str
    scenario_id: str
    shop: List[EquipmentTemplateModel]
    turn: int
