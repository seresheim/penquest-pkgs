from dataclasses import dataclass

@dataclass
class PostGameSummaryModel():
    end_state: int
    turns_played: int
    attacker_undetected_turns: int
    actions_detected: int
    damage_dealt: int
    damage_healed: int
    equipment_purchased: int
    credits_spent: float
    actions_succeeded: int
    credits_spent_total: float