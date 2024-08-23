from enum import Enum

class GameEndedState(Enum):
    WON = 1
    LOST = 2
    DRAW = 3
    SURRENDERED = 4