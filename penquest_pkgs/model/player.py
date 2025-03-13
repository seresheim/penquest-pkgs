from dataclasses import dataclass


@dataclass()
class PlayerModel():
    id: int
    connection_id: str
    name: str
    online: bool
    user_id: str
    rank: int
    avatar_id: str = None