from dataclasses import dataclass, field
from typing import Dict, List

from penquest_pkgs.model.player import Player
from penquest_pkgs.model.game_options import GameOptions
from penquest_pkgs.model.game_option_locks import GameOptionLocks
from penquest_pkgs.model.scenario_teaser import ScenarioTeaser
from penquest_pkgs.model.goal_desc import GoalDesc


@dataclass()
class Lobby():
    admin :Player
    code :str
    game_options :GameOptions
    gameOptionLocks :GameOptionLocks
    players :Dict[int, Player] = field(default_factory=dict)
    scenario :ScenarioTeaser = None
    availableGoals :List[GoalDesc] = field(default_factory=list)