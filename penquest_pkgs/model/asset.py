from dataclasses import dataclass
from typing import List

from penquest_pkgs.model.action import Action
from penquest_pkgs.model.effect import Effect
from penquest_pkgs.model.equipment import Equipment


@dataclass()
class Asset():
    # most nullable parameters are because of the asset object in the goal that
    # is basically empty except for the id. Once this is changed to ID and Name
    # only, these nullables can be removed again.
    id :int
    name :str
    category :int
    attack_stage :int
    active_exploits :List[Equipment]
    hasAdminRights :bool
    isOffline :bool

    description :str = None
    initially_exposed :bool = None
    os :int = None
    parent_asset :int = None
    child_assets :List[int] = None
    exposed :List[bool] = None
    damage :List[int] = None
    attack_vectors :List[int] = None
    dependencies :List[int] = None
    permanent_effects :List[Effect] = None
    hasBeenSeen :bool = None
    played_actions :List[Action] = None
    shield :bool = None
    hasBeenSeen :bool = None


    def __eq__(self, other):
        if not isinstance(other, Asset):
            return False
        return self.id == other.id