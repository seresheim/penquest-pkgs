from dataclasses import dataclass
from typing import List


@dataclass()
class ActionEventModel():
    #action: "ActionModel"
    turn_detected: int
    succeeded: bool
    deflected: int
    deflected_by: List["ActionTemplateModel"]
    deflected_damage: "DamageModel"
    asset_id: int = None
    current_asset_damage: "DamageModel" = None
    applied_dependency_damage: List[int] = None
    damage_dealt: "DamageModel" = None
    active_damage: "DamageModel" = None
    countered: List[int] = None
    fully_countered: bool = None
    counters: int = None
    is_counterable: bool = None
    last_turn_to_counter: int = None
    attack_mask_used: str = None

    def is_currently_counterable(self, game_state: "GameStateModel") -> bool:
        if not self.is_counterable:
            return False
        if game_state.turn > self.last_turn_to_counter:
            return False
        return True