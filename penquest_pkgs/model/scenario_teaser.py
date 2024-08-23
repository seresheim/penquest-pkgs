from dataclasses import dataclass
from typing import List

from penquest_pkgs.model.slot_info import SlotInfo


@dataclass()
class ScenarioTeaser():
    id :str
    name :str
    description :str
    availableSlots :List[SlotInfo]