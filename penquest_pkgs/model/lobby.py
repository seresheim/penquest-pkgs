from dataclasses import dataclass, field
from typing import Dict, List

from penquest_pkgs.model import (
    PlayerModel,
    GameOptionsModel,
    GameOptionLocksModel,
    ScenarioTeaserModel,
    GoalDescModel
)


@dataclass()
class LobbyModel():
    admin: PlayerModel
    code: str
    game_options: GameOptionsModel
    game_option_locks: GameOptionLocksModel
    players: Dict[int, PlayerModel] = field(default_factory=dict)
    scenario: ScenarioTeaserModel = None
    available_goals: List[GoalDescModel] = field(default_factory=list)
    xp_event: str = None
    seed: int = None