from dataclasses import dataclass

from penquest_pkgs.constants import VALID_ATTACK_MASKS
from penquest_pkgs.exceptions import PenQuestException, Errors

@dataclass()
class ExposedModel():
    C: bool = False
    I: bool = False
    A: bool = False

    
    def is_exposed(self, c: str) -> bool:
        c = c.upper()
        if c == 'C':
            return self.C
        elif c == 'I':
            return self.I
        elif c == 'A':
            return self.A
        raise PenQuestException(
            Errors.InvalidAttackMaskError,
            f"Invalid attack mask: {c}"
        )
    
    def to_cia_str(self):
        return ''.join([
            'C' if self.C else '',
            'I' if self.I else '',
            'A' if self.A else ''
        ])
    
    def __str__(self):
        return self.to_cia_str()
    
    def to_mulit_binary(self):
        return [
            int(1 if self.C else 0),
            int(1 if self.I else 0),
            int(1 if self.A else 0)
        ]