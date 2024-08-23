from dataclasses import dataclass
from typing import List

from penquest_pkgs.model.effect import Effect

@dataclass()
class Equipment():
    id :int
    # TODO: check up with Thomas
    template_id :str
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
    active :bool = None
    equipt_on_action :int = None
    equipt_on_asset :int = None
    possible_actions :List[str] = None
    used_on_action :int = None
    used_on_asset :int = None
    owner :int = None

    def __eq__(self, other):
        if not isinstance(other, Equipment):
            return False
        return self.id == other.id
    
    def __str__(self):
        return f"{self.name}({self.template_id}|{self.id})"
    
    def __repr__(self):
        return f"{self.name}({self.template_id}|{self.id})"