from dataclasses import dataclass


@dataclass
class GoalDesc():
    id :str
    description :str
    isDefault :bool