from enum import Enum


class ActionSuccessMode(Enum):
    DEFAULT = 0
    ALWAYS_SUCCESS = 1

class ActionDetectionMode(Enum):
    DEFAULT = 0
    ALWAYS_DETECT = 1

class EquipmentShopMode(Enum):
    DISABLED = 0
    RANDOM = 1
    ALL_EQUIPMENT = 2

class ActionShopMode(Enum):
    RANDOM = 0
    ALL_ACTIONS = 1

class SupportActionsMode(Enum):
    DISABLED = 0
    ENABLED = 1
    ALL_AT_START = 2

class InitActionsMode(Enum):
    RANDOM = 0
    PLAYABLE = 1
    PICK = 2

class InitialAssetStage(Enum):
    DEFAULT = 0
    RECONNAISSANCE = 1
    INITIAL_ACCESS = 2
    EXECUTION = 3

class ManualDefType(Enum):
    DISABLED = 0
    PREVENTION = 1
    DETECTION = 2
    RESPONSE = 3
    PREVENTION_ONLY = 4
    DETECTION_ONLY = 5
    RESPONSE_ONLY = 6

class MultiTargetSuccess(Enum):
    ONE_PER_TARGET = 0
    ONE_FOR_ATTACKERS = 1
    ONE_FOR_DEFENDERS = 2
    ONE_FOR_ALL = 3

class DefenderActionsDetectable(Enum):
    RESPONSE_ONLY = 0
    PREVENTION_RESPONSE = 1
    DETECTION_RESPONSE = 2
    ALL = 3

class DefenderAvailibilityPenalty(Enum):
    ENABLED = 0
    DISABLED = 1
