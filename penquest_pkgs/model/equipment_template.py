from dataclasses import dataclass
from typing import List

from penquest_pkgs.model.effect import Effect


@dataclass()
class EquipmentTemplate():
    id :str
    type :str
    name :str
    short_description :str
    long_description :str
    price :float
    isPassiveEquipment :bool
    isSingleUse :bool
    impact :List[int] = None
    effects :List[Effect] = None
    transfer_effects :List[Effect] = None
    possible_actions :List[str] = None