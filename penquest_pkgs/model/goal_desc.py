from dataclasses import dataclass


@dataclass
class GoalDescModel():
    id: str
    description: str
    is_default: bool