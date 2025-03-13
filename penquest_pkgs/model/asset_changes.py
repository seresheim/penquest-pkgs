from dataclasses import dataclass
from typing import List
from penquest_pkgs.model import AssetModel

@dataclass
class AssetChangesModel():
    hidden: List[int]
    revealed: List[AssetModel]