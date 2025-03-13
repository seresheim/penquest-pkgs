from penquest_pkgs.model import GameStateModel
from penquest_pkgs.constants import (
    GameInteractionType, 
    GamePhase, 
    GameInteractionPhase, 
    EquipmentShopMode
)
from penquest_pkgs.utils.logging import get_logger


from typing import Optional
import dataclasses



class GameInteraction:

    @staticmethod
    def is_interaction_valid(
        game_state: GameStateModel,
        interaction: GameInteractionType
    ) -> bool:
        """Checks whether the interaction provided is valid in the current
        game state, especially in the current game interaction phase.

        :param game_state: _description_
        :param int_type: _description_
        :return: _description_
        """
        if game_state.interaction_phase == GameInteractionPhase.Idle:
            # FinishTurn is a PLAY_CARD interaction but raised during Idle
            return interaction == GameInteractionType.PLAY_CARD
        elif game_state.interaction_phase == GameInteractionPhase.Shopping:
            return interaction == GameInteractionType.SHOPPING_PHASE
        elif game_state.interaction_phase == GameInteractionPhase.Redrawing:
            return interaction == GameInteractionType.CHOOSE_ACTION
        elif game_state.interaction_phase == GameInteractionPhase.Playing:
            return interaction == GameInteractionType.PLAY_CARD
        return False
    
    @staticmethod
    def get_interaction(game_state: GameStateModel) -> Optional[GameInteractionType]:
        """Returns the current interaction type based on the current game
        interaction phase.

        :param game_state: the current game state
        :return: the interaction type that is valid in the current game state
        """
        if game_state.game_phase == GamePhase.Ended:
            return GameInteractionType.END
        elif game_state.game_phase == GamePhase.InitDraw:
            return GameInteractionType.CHOOSE_ACTION
        elif game_state.interaction_phase == GameInteractionPhase.Idle:
            return None
        elif game_state.interaction_phase == GameInteractionPhase.Shopping:
            return GameInteractionType.SHOPPING_PHASE
        elif game_state.interaction_phase == GameInteractionPhase.Redrawing:
            return GameInteractionType.CHOOSE_ACTION
        elif game_state.interaction_phase == GameInteractionPhase.Playing:
            return GameInteractionType.PLAY_CARD
        return None
    
    @staticmethod
    def move_from_idle(game_state: GameStateModel) -> GameStateModel:
        """Moves the game state from the idle phase to the next phase.

        :param game_state: the current game state
        :return: the updated game state
        """
        if game_state.turn == 1:
            if game_state.game_phase in [GamePhase.DefenderPreSetup, GamePhase.InitDraw]:
                new_phase = GameInteractionPhase.Redrawing
            elif game_state.game_options.equipment_shop_mode == EquipmentShopMode.DISABLED:
                new_phase = GameInteractionPhase.Playing
            else:
                new_phase = GameInteractionPhase.Shopping
        else:
            # in case the agent didn't play a card in the previous turn there is
            # nothing to redraw, hence skip the interaciton phase redrawing
            if len(game_state.selection_choices) > 0:
                new_phase = GameInteractionPhase.Redrawing
            elif game_state.game_options.equipment_shop_mode == EquipmentShopMode.DISABLED:
                new_phase = GameInteractionPhase.Playing
            else:
                new_phase = GameInteractionPhase.Shopping

        game_state = dataclasses.replace(
            game_state, 
            interaction_phase=new_phase
        )
        get_logger(__name__, game_state.connection_id, game_state.name, game_state.role.type).debug(
            f"Game interaction phase changed: {new_phase}"
        )
        return game_state
    
    @staticmethod
    def move_from_redrawing(game_state: GameStateModel) -> GameStateModel:
        """Moves the game state from the redrawing phase to the next phase.

        :param game_state: the current game state
        :return: the updated game state
        """
        if game_state.game_phase == GamePhase.InitDraw:
            new_phase = GameInteractionPhase.Idle
        elif game_state.game_options.equipment_shop_mode == EquipmentShopMode.DISABLED:
            new_phase = GameInteractionPhase.Playing
        else:
            new_phase = GameInteractionPhase.Shopping
        game_state = dataclasses.replace(
            game_state, 
            interaction_phase=new_phase
        )
        get_logger(__name__, game_state.connection_id, game_state.name, game_state.role.type).debug(
            f"Game interaction phase changed: {new_phase}"
        )
        return game_state
    
    @staticmethod
    def move_from_shopping(game_state: GameStateModel) -> GameStateModel:
        """Moves the game state from the shopping phase to the next phase.

        :param game_state: the current game state
        :return: the updated game state
        """
        new_phase = GameInteractionPhase.Playing
        game_state = dataclasses.replace(
            game_state, 
            interaction_phase=new_phase
        )
        get_logger(__name__, game_state.connection_id, game_state.name, game_state.role.type).debug(
            f"Game interaction phase changed: {new_phase}"
        )
        return game_state
    
    @staticmethod
    def move_from_playing(game_state: GameStateModel) -> GameStateModel:
        """Moves the game state from the playing phase to the next phase.

        :param game_state: the current game state
        :return: the updated game state
        """
        new_phase = GameInteractionPhase.Idle
        game_state = dataclasses.replace(
            game_state, 
            interaction_phase=new_phase
        )
        get_logger(__name__, game_state.connection_id, game_state.name, game_state.role.type).debug(
            f"Game interaction phase changed: {new_phase}"
        )
        return game_state