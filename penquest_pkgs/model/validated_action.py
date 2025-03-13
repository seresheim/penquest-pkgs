from dataclasses import dataclass, field
from typing import List, Optional
from penquest_pkgs.model import ActionModel
from penquest_pkgs.exceptions import PenQuestException

@dataclass()
class ValidatedActionModel():
    action: ActionModel
    errors: Optional[List[PenQuestException]] = field(default_factory=lambda:[])
    warnings: Optional[List[Warning]] = field(default_factory=lambda:[])

    def is_playable(self) -> bool:
        """Determines whether a validated action is playable by checking if
        any errors appeared during the checks

        Returns:
            bool: indicates whether the validated action is playable
        """
        return len(self.errors) == 0