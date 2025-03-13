from dataclasses import dataclass
from typing import List

from penquest_pkgs.model import SlotInfoModel


@dataclass()
class ScenarioTeaserModel():
    id: str
    name: str
    description: str
    available_slots: List[SlotInfoModel]