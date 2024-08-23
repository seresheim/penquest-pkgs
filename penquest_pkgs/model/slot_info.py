from dataclasses import dataclass

@dataclass()
class SlotInfo():
    slotId :int
    name :str
    type :int
    isReady :bool