from dataclasses import dataclass


@dataclass()
class Player():
    id :int
    connection_id :str
    name :str
    online :bool
    user_id :str
    avatar_id :int = None