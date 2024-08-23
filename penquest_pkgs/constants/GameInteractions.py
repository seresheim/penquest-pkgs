from enum import Enum

class GameInteractionType(Enum):
    """Enum for the different types of interactions that can occur in the game."""
    CREATE_OR_JOIN_LOBBY = 0
    CHANGE_LOBBY_PROPERTIES = 1
    PLAYER_READY = 2

    SHOPPING_PHASE = 3
    PLAY_CARD = 4
    CHOOSE_ACTION = 5
    END = 6

    @classmethod
    def get_interaction_type(cls, interaction_type: int) -> str:
        map = {
            0: 'CREATE_OR_JOIN_LOBBY',
            1: 'CHANGE_LOBBY_PROPERTIES',
            2: 'PLAYER_READY',
            3: 'SHOPPING_PHASE',
            4: 'PLAY_CARD',
            5: 'CHOOSE_ACTION',
            6: 'END',
        }
        return map[interaction_type]
