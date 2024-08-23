from dataclasses import dataclass
from typing import List, Dict

from penquest_pkgs.model.action_template import ActionTemplate
from penquest_pkgs.model.actor import Actor
from penquest_pkgs.model.equipment_template import EquipmentTemplate
from penquest_pkgs.model.player import Player


@dataclass()
class Game():
    actions_offered :List[ActionTemplate]
    amount_selection :int
    phase :str
    players :List[Player]
    roles :Dict[str, Actor]
    scenarioDescription :str
    scenarioName :str
    scenario_id :str
    shop :List[EquipmentTemplate]
    turn :int
