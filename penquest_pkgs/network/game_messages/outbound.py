from typing import List, Dict
from dataclasses import dataclass

from penquest_pkgs.model.game_options import GameOptions
import penquest_pkgs.network.game_messages.message_models as mm


def dataclass_to_dict(instance):
    if isinstance(instance, (list, tuple)):
        return [dataclass_to_dict(item) for item in instance]
    elif isinstance(instance, dict):
        return {k: dataclass_to_dict(v) for k, v in instance.items()}
    elif hasattr(instance, '__dict__'):
        return {
            k: dataclass_to_dict(v) 
            for k, v in instance.__dict__.items() 
            if not k.startswith('__')
        }
    else:
        return instance

@dataclass()
class OutboundMessage():
    
    def __init__(self, **kwargs):
        pass

@dataclass()
class JoinLobbyMessage(OutboundMessage):
    code: str

@dataclass()
class PlayersChangedMessage(OutboundMessage):
    players: Dict[int, mm.Player]


@dataclass()
class LobbyChangedMessage(OutboundMessage):
    lobby: mm.Lobby

@dataclass()
class SetSeedMessage(OutboundMessage):
    seed: int



@dataclass()
class SetGoalMessage(OutboundMessage):
    goalId: str


@dataclass()
class SelectScenarioMessage(OutboundMessage):
    scenario_id: str


@dataclass()
class UpdateGameOptionsMessage(OutboundMessage):
    game_options: GameOptions


@dataclass()
class AddBotMessage(OutboundMessage):
    slot: int
    type: int


@dataclass()
class SetPlayerReadinessMessage(OutboundMessage):
    ready: bool


@dataclass()
class ChangeSlotMessage(OutboundMessage):
    new_slot: int


@dataclass()
class GetValidActionsMessage(OutboundMessage):
    actions: List[Dict[str, int]]


@dataclass()
class SelectActionsMessage(OutboundMessage):
    action_ids: List[int]


@dataclass()
class PlayActionMessage(OutboundMessage):
    action_id: int
    target_asset_id: int
    attack_mask: str
    support_action_ids: List[int] = None
    equipment_ids: List[int] = None
    response_target_id: int = 0


@dataclass()
class BuyEquipmentMessage(OutboundMessage):
    equipment: List[int]
    endShopping: bool = True
