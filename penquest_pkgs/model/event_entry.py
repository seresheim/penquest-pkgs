from dataclasses import dataclass

@dataclass()
class EventEntryModel():
    id: int
    created: str
    type: int