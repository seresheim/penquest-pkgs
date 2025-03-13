from dataclasses import dataclass, field
from typing import Optional, Dict, List


from penquest_pkgs.constants import GamePhase, GameInteractionPhase, GameEndedState
from penquest_pkgs.model import (
    PlayerModel,
    GameOptionsModel,
    ScenarioTeaserModel,
    LobbyModel,
    EquipmentModel,
    ActionModel,
    AssetModel,
    ActorModel,
)
from penquest_pkgs.model.validated_play_action import ValidatedPlayActionModel
import pandas as pd


@dataclass(frozen=True)
class GameStateModel:
    # Lobby specific state
    name: str                                = field(default=None)
    scenario: ScenarioTeaserModel            = field(default=None)
    from_lobby: Optional[LobbyModel]         = field(default=None)
    game_options: GameOptionsModel           = field(default_factory=lambda: GameOptionsModel())

    # Player specific state
    actor_id: Optional[int]             = field(default=None)
    connection_id: Optional[str]  = field(default=None)
    players: List[PlayerModel]               = field(default_factory=lambda: [])
    
    # Overall game state
    turn: int                           = field(default=1)
    game_phase: GamePhase   = field(default=GamePhase.Starting)
    interaction_phase: GameInteractionPhase   = field(default=GameInteractionPhase.Idle)
    end_state: Optional[GameEndedState] = field(default=None)
    roles: Dict[str, ActorModel]             = field(default_factory=lambda: {})
    
    # Game board changes
    shop: List[EquipmentModel]               = field(default_factory=lambda: [])
    hand: List[ActionModel]                  = field(default_factory=lambda: [])
    equipment: List[EquipmentModel]          = field(default_factory=lambda: [])
    assets_on_board: List[AssetModel]        = field(default_factory=lambda: [])

    # Only used when a selection is required
    selection_choices: List[ActionModel]     = field(default_factory=lambda: [])
    selection_amount: int               = field(default=-1)

    # Only used when an action is played
    playable_actions: pd.DataFrame = field(default_factory=lambda: pd.DataFrame([[]]))
    # main action idx, target asset id, attack mask idx, support action idx, equipment idx

    discovered: bool                    = field(default=False)
    action_points: int                  = field(default=5)
    actions_played_this_turn: int       = field(default=0)

    validated_actions: List[ValidatedPlayActionModel] = field(default_factory=lambda: [])

    @property
    def role(self) -> Optional[ActorModel]:
        if self.connection_id in self.roles:
            return self.roles[self.connection_id]
        return None
        
    
    
        