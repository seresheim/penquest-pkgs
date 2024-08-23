from dataclasses import dataclass, field
from typing import Optional, Dict, List

from penquest_pkgs.constants.GameEndedState import GameEndedState
from penquest_pkgs.model.game_options import GameOptions
from penquest_pkgs.model.game_phase import ExternalGamePhase, InternalGamePhase
from penquest_pkgs.model.action import Action
from penquest_pkgs.model.equipment import Equipment
from penquest_pkgs.model.asset import Asset
from penquest_pkgs.model.scenario_teaser import ScenarioTeaser
from penquest_pkgs.model.lobby import Lobby
from penquest_pkgs.model.player import Player


@dataclass(frozen=True)
class GameState:
    # Lobby specific state
    name: str
    scenario: ScenarioTeaser
    from_lobby: Optional[Lobby]         = field(default=None)
    game_options: GameOptions           = field(default_factory=lambda: GameOptions())

    # Player specific state
    actor_id: Optional[int]             = field(default=None)
    actor_connection_id: Optional[str]  = field(default=None)
    players: List[Player]               = field(default_factory=lambda: [])
    
    # Overall game state
    turn: int                           = field(default=1)
    external_phase: ExternalGamePhase   = field(default=ExternalGamePhase.Starting)
    internal_phase: InternalGamePhase   = field(default=InternalGamePhase.Idle)
    end_state: Optional[GameEndedState]             = field(default=None)
    roles: Dict                         = field(default_factory=lambda: {})
    
    # Game board changes
    shop: List                          = field(default_factory=lambda: [])
    hand: List[Action]                  = field(default_factory=lambda: [])
    equipment: List[Equipment]          = field(default_factory=lambda: [])
    assets_on_board: List[Asset]        = field(default_factory=lambda: [])

    # Only used when a selection is required
    selection_choices: List             = field(default_factory=lambda: [])
    selection_amount: int               = field(default=0)
        
    
    
        