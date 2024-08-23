from enum import Enum

class GameStoragePhase(Enum):
    Start = 0
    Lobby = 1
    Running = 2
    Ended = 3