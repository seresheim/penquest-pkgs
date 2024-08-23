from enum import Enum


class ExternalGamePhase(Enum):
    Starting = 0
    InitDraw = 1
    Attacker = 3
    Defender = 4
    Ended = 5

class InternalGamePhase(Enum):
    Idle = 0
    Shopping = 1
    Playing = 2