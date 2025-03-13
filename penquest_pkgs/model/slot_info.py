from dataclasses import dataclass

@dataclass()
class SlotInfoModel():
    slot_id: int
    name: str
    type: int
    is_ready: bool