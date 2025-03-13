from typing import List

class AttackStage:
    RECONNAISSENCE = 1
    INITIAL_ACCESS = 2
    EXECUTION = 3

    @staticmethod
    def get_all_stages() -> List["AttackStage"]:
        return [
            AttackStage.RECONNAISSENCE,
            AttackStage.INITIAL_ACCESS,
            AttackStage.EXECUTION
        ]