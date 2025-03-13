from typing import Tuple, List, Optional
import itertools

from penquest_pkgs.model import (
    GameStateModel,
    ActionModel,
    AssetModel,
    EquipmentModel,
    EquipmentTemplateModel,
    ValidatedRedrawActionModel,
    ValidatedPlayActionModel,
)
from penquest_pkgs.utils import get_logger
from penquest_pkgs.constants import (
    VALID_ATTACK_MASKS,
    CIA,
    CardType,
    PERMANENT_EQUIPMENT_TYPES,
    TargetType,
    DefType,
    EMPTY_ATTACK_MASK,
    C,
    I,
    A,
)
from penquest_pkgs.game.action_helper import ActionHelper
from penquest_pkgs.game.actor_helper import ActorHelper
from penquest_pkgs.game.action_validation_helper import (
    ActionValidationHelper,
    ActionValidatorOptions,
)
from penquest_pkgs.exceptions import PenQuestException, Errors

class GameHelper():
    """Helps extract additional information from the current game state. Methods
    of this class do not alter the game state """

    @staticmethod
    def get_playable_actions(game_state: GameStateModel) -> List[ActionModel]:
        """Returns a list of currently playable actions the actor holds on its
        hand. This does not specify whether the action is playable on a specific
        asset or not. this method is not suitable to evaluate new actions for 
        redrawing.
        """

        playable_combinations = game_state.playable_actions

        if playable_combinations.empty or playable_combinations.size == 0:
            get_logger(__name__, game_state.connection_id, game_state.name, game_state.role.type).debug(
                "No playable actions available. Probably due to not enough APs "
                f"Current APs: {game_state.action_points}"
            )
            return []

        # gets all unique values of the first column of the DataFrame and sorts
        # them
        sorted_idxs = sorted(
            playable_combinations.iloc[:, 0].unique().tolist()
        )
        playable_actions = [
            game_state.hand[idx] for idx in sorted_idxs
        ]

        return playable_actions

    @staticmethod
    def get_targets(
            game_state: GameStateModel,
            action: ActionModel
        ) -> List[AssetModel]:
        """Returns a list of assets that are possible targets for the provided
        action"""

        pa = game_state.playable_actions
        action_idx = game_state.hand.index(action)
        relevant_actions = pa[pa[0] == action_idx]
        sorted_ids = sorted(relevant_actions[1].unique().tolist())
        possible_targets = [
            GameHelper.get_asset(game_state, asset_id) for asset_id in sorted_ids
        ]

        if possible_targets is None:
            return []

        possible_targets = [a for a in possible_targets if a is not None]

        return possible_targets

    @staticmethod
    def get_attack_masks(
        game_state: GameStateModel, 
        action: ActionModel
        ) -> List[str]:
        """Returns a list of attack masks that are possible for the provided
        action"""
        pa = game_state.playable_actions
        relevant_actions = pa[pa[0] == action.id]
        sorted_idxs = sorted(relevant_actions[2].unique().tolist())
        attack_masks = [VALID_ATTACK_MASKS[idx] for idx in sorted_idxs]

        return attack_masks

    @staticmethod
    def get_response_target_ids(
        game_state: GameStateModel,
        action: ActionModel
        ) -> List[int]:
        """Returns a list of integers that represent action ids of attack
        actions the provided defence action can counter. Returns a list of
        all possible response target ids across all assets
        """
        response_target_ids_set = set()
        pa = game_state.playable_actions

        # filter for provided action
        relevant_actions = pa[pa[0] == action.id]
        # filter for response target ids that are relevant (greater than 0)
        response_targets = relevant_actions[relevant_actions[5] > 0]
        if len(response_targets) == 0:
            return []
        response_target_ids = sorted(response_targets[5].unique().tolist())

        return response_target_ids

    @staticmethod
    def get_target_response_target_pairs(
        game_state: GameStateModel,
        action: ActionModel
        ) -> List[Tuple[AssetModel, int]]:
        """Returns a list of integers that represent action ids of attack
        actions the provided defence action can counter. Returns a list of
        all possible response target ids across all assets
        """
        pa = game_state.playable_actions

        # filter for provided action
        relevant_actions = pa[pa[0] == action.id]
        # select columns 'target asset' and 'response target id'
        response_target_id_pairs = list(
            relevant_actions.iloc[:, [1, 5]].itertuples(index=False, name=None)
        )

        response_target_pairs = [
            (GameHelper.get_asset(game_state, a_id), rt_id)
            for a_id, rt_id in response_target_id_pairs
        ]

        return response_target_pairs

    @staticmethod
    def get_combinations(
        game_state: GameStateModel,
        actions: List[ActionModel]=None,
        assets: List[AssetModel]=None,
        attack_masks: List[str]=None
        ) -> List[Tuple[ActionModel, AssetModel, str, Optional[ActionModel], Optional[EquipmentModel], Optional[int]]]:
        """Retrieves a list of valid action combination with objects instead of
        integers that represent indices or IDs. The list can be filtered for
        specific actions, assets, or attack masks."""
        pa = game_state.playable_actions

        # filter for provided action
        if actions is not None:
            idxs = [game_state.hand.index(a) for a in actions]
            pa = pa[pa[0].isin(idxs)]

        # filter for provided asset
        if assets is not None:
            asset_ids = [asset.id for asset in assets]
            pa = pa[pa[1].isin(asset_ids)]

        # filter for provided attack mask
        if attack_masks is not None:
            idxs = [VALID_ATTACK_MASKS.index(a) for a in attack_masks]
            pa = pa[pa[2].isin(idxs)]
        
        # transform DataFrame to list of tuples
        idx_combinations = list(pa.itertuples(index=False, name=None))

        object_combinations = [
            (
                game_state.hand[ac_idx],
                GameHelper.get_asset(game_state, as_id),
                VALID_ATTACK_MASKS[mask_idx],
                game_state.hand[supp_idx-1] if supp_idx > 0 else None,
                game_state.equipment[eq_idx-1] if eq_idx > 0 else None,
                rt_id if rt_id > 0 else None
            ) 
            for ac_idx, as_id, mask_idx, supp_idx, eq_idx, rt_id in idx_combinations
        ]

        return object_combinations

    @staticmethod
    def objects_to_idxs(
        game_state: GameStateModel,
        combination: Tuple[ActionModel, AssetModel, str, Optional[ActionModel], Optional[EquipmentModel], Optional[int]]
        ) -> Tuple[int, int, int, int, int, int]:
        """Transforms a playable combination of ActionModel, AssetModel, etc. objects to 
        a combination of indices/IDs
        """
        m_action, t_asset, mask, s_action, eq, r_target = combination
        m_action_idx = game_state.hand.index(m_action)
        t_asset_id = t_asset.id if t_asset is not None else 0
        mask_idx = VALID_ATTACK_MASKS.index(mask)
        # .index() starts counting at 0, but base_strategy requires to start
        # counting support actions and equipment at 1, therefore add 1
        s_action_idx = game_state.hand.index(s_action)+1 if s_action is not None else 0
        eq_idx = game_state.equipment.index(eq)+1 if eq is not None else 0
        r_target_id = r_target if r_target is not None else 0

        return m_action_idx, t_asset_id, mask_idx, s_action_idx, eq_idx, r_target_id

    @staticmethod
    def get_eq_playable_actions(
        game_state: GameStateModel,
        actions: List[ActionModel]
        ) -> List[ActionModel]:
        """Filters a list of actions for actions that do not have any missing 
        equipment requirements, in other words, that are playable"""
        return [
            action for action in actions 
            if GameHelper.have_req_eq(game_state, action)
        ]

    @staticmethod
    def get_eq_not_playable_actions(
        game_state: GameStateModel,
        actions: List[ActionModel]
        ) -> List[ActionModel]:
        """Filters a list of actions for actions that do have missing 
        equipment requirements, in other words, that are not playable"""
        return [
            action for action in actions 
            if not GameHelper.have_req_eq(game_state, action)
        ]

    @staticmethod
    def have_req_eq(game_state: GameStateModel, action: ActionModel) -> bool:
        """Checks if the player has the equipment that is required for the 
        provided action
        """
        if len(action.required_equipment) == 0:
            return True

        eq_template_ids = set([eq.template_id for eq in game_state.equipment])
        if any([req_eq.id in eq_template_ids for req_eq in action.required_equipment]):
            return True

        return False

    @staticmethod
    def get_asset(
        game_state: GameStateModel,
        asset_id: int
        ) -> Optional[AssetModel]:
        """Returns the asset with the provided id"""
        for asset in game_state.assets_on_board:
            if asset.id == asset_id:
                return asset
        return None

    @staticmethod
    def action_playable_on_asset(action: ActionModel, asset: AssetModel) -> bool:
        """Checks if the provided action is playable on the provided asset"""
        return asset.category in action.asset_categories and \
            asset.os in action.oses and asset.attack_stage >= action.attack_stage

    @staticmethod
    def check_for_required_equipment(
        actions: List[ActionModel],
        equipment: List[EquipmentModel],
        shop: List[EquipmentTemplateModel]
        ) -> List[Tuple[EquipmentTemplateModel]]:
        """Checks if the player has all the required equipment for the provided
        actions. If not, returns a list of the missing equipment templates.

        :param actions: List of actions that should be checked for required
            equipment
        :param equipment: List of equipment that the player owns
        :param shop: List of equipment templates that is available in the shop
        :return: List of tuples of equipment templates. All templates within a
            tuple are alternatives for a single action. 
        """

        missing_total_req_eq = []
        shop_tids = [eq.id for eq in shop]
        for action in actions:
            required_tids = [eq.id for eq in action.required_equipment]
            already_owned_equipment = [
                eq for eq in equipment if eq.template_id in required_tids
            ]

            if len(required_tids) == 0:
                # there is no equipment required to play the action
                continue
            if len(already_owned_equipment) > 0:
                # player already owns one of the required equipment
                continue

            missing_reqs = tuple([
                eq for eq in action.required_equipment if eq.id in shop_tids
            ])
            if len(missing_reqs) > 0:
                missing_total_req_eq.append(missing_reqs)
        return missing_total_req_eq

    @staticmethod
    def check_response_compatability(
        action: ActionModel,
        asset: AssetModel
        ) -> bool:
        """Checks if the provided defense action is compatible with the 
        provided asset and whether the defense action is able to heal damage
        that was previously done to the asset"""

        # TODO: check for response targets on the asset an whether these
        # targets can still be responded to

        if not asset.category in action.asset_categories:
            return False
        if not asset.os in action.oses:
            return False

        dmg_mask = [CIA[i] for i,dmg in enumerate(asset.damage) if dmg > 0]
        if action.predefined_attack_mask:
            # check if predefined attack mask of action matches the damage that
            # was done on the asset
            if not any(char for char in action.predefined_attack_mask if char in dmg_mask):
                return False
        else:
            # check if action can heal something of the asset's damage
            if not any(action.impact[i] < 0 for i, dmg in enumerate(asset.damage) if dmg > 0):
                return False
        return True

    @staticmethod
    def get_affordable_equipment(
        eq_list: List[EquipmentModel],
        pq_credits: float
        ) -> List[EquipmentModel]:
        """Selects equipment from a list as long as credits are available and
        there is affordable equipment left to select. Returns the list of
        equipment to buy and the remaining credits.

        :param eq_list: List of equipment objects the bot can select from
        :param credits: Amount of credits the bot currently has available
        :return: List of selected equipment, remaining credits
        """
        shopping_list = []

        # if player has no credits anymore, player cannot buy any equipment
        if pq_credits == 0.0:
            return [], 0.0

        # if there is no equipment left to buy, player cannot buy any equipment
        if len(eq_list) == 0:
            return [], pq_credits

        # check if player can afford at least one item (the cheapest)
        cheapest_eq = min(eq_list, key=lambda x: x.price)
        if cheapest_eq.price > pq_credits:
            return [], pq_credits

        while len(eq_list) > 0 and cheapest_eq.price <= pq_credits and pq_credits > 0:
            eq = eq_list.pop()
            if eq.price <= pq_credits:
                pq_credits -= eq.price
                shopping_list.append(eq)
                if cheapest_eq.id == eq.id and len(eq_list) > 0:
                    cheapest_eq = min(eq_list, key=lambda x: x.price)
        return shopping_list, pq_credits

    @staticmethod
    def get_cheapest_required_equipment(
        game_state: GameStateModel
        ) -> List[EquipmentTemplateModel]:
        """Returns a list of the cheapest equipment that is required
        to play an action currently on the hand. Only so much equipment is 
        selected that can actually be bought with the current credits.
        """
        shopping_list = []

        missing_total_req_eq = GameHelper.check_for_required_equipment(
            game_state.hand,
            game_state.equipment,
            game_state.shop
        )
        pq_credits = game_state.role.credits

        for eq_tuple in missing_total_req_eq:
            # determine the cheapest equipment of the tuple
            sorted_eqs = sorted(eq_tuple, key=lambda x: x.price)
            if len(sorted_eqs) > 0:
                eq = sorted_eqs[0]
                if pq_credits < eq.price:
                    shopping_list.append(eq)
                    pq_credits -= eq.price

        return shopping_list

    @staticmethod
    def get_all_action_combs(
            game_state: GameStateModel
        ) -> List[Tuple[ActionModel,ActionModel,EquipmentModel]]:
        """Returns all combinations of main actions, support actions, equipment 
        and attack masks

        :return: list of main_action - support_action - equipment triplets,
            None indicates no support action or equipment
        """

        main_actions = [
            action
            for action in game_state.hand
            if action.card_type == CardType.MAIN
        ]
        support_actions = [
            action
            for action in game_state.hand
            if action.card_type == CardType.SUPPORT
        ]
        # add option "no support action"
        support_actions.append(None)
        # Exclude permanent equipments from validation
        equipments = [
            eq
            for eq in game_state.equipment
            if eq.type not in PERMANENT_EQUIPMENT_TYPES
        ]
        # add option "no equipment"
        equipments.append(None)
        
        return list(
            itertools.product(
                main_actions,
                support_actions,
                equipments
            )
        )

    @staticmethod
    def get_possible_response_targets(
            game_state: GameStateModel,
            main_action: ActionModel,
            asset: AssetModel,
            attack_mask: str = None,
        ) -> List[ActionModel]:
        """Retrieves a list of possible response targets for a provided defense
        action that can be countered by the defense action. The response targets
        are determined by the attack mask of the defense action and the attack
        masks of all attack actions that have been played on the asset.

        Args:
            game_state (GameStateModel): state of the game
            main_action (ActionModel): defense action for which possible response
                targets are determined
            asset (AssetModel): asset on which the defense action is played
            attack_mask (str, optional): attack mask that . Defaults to None.

        Returns:
            List[ActionModel]: list of possible response targets
        """
        possible_response_targets = []

        if attack_mask is None or attack_mask == "":
            attack_mask = CIA

        if main_action.has_heal_part:
            self_attack_mask = set(attack_mask)
            for action in asset.played_actions:
                event = ActionHelper.get_event(action, asset.id)
                if event.attack_mask_used is None:
                    other_attack_mask = ""
                else:
                    other_attack_mask = set(event.attack_mask_used)
                inter_mask_chars = [c for c in self_attack_mask if c in other_attack_mask]
                inter_attack_mask = "".join(inter_mask_chars)
                if event.asset_id is not None and \
                    not event.fully_countered and \
                    any([i > 0 for i in event.active_damage]) and \
                    (action.template_id in main_action.affected_attack_actions or \
                     action.template_id in main_action.affected_defense_actions) and \
                    len(inter_attack_mask) > 0 and \
                    any([c < 0 for c in main_action.impact.apply_mask(inter_attack_mask)]):
                    if event.is_currently_counterable(game_state):
                        possible_response_targets.append(action)
        return possible_response_targets

    @staticmethod
    def get_valid_play_action_combs(
            game_state: GameStateModel,
            combos: List[Tuple[ActionModel,ActionModel,EquipmentModel]]
        ) -> List[ValidatedPlayActionModel]:
        """_summary_

        Args:
            game_state (GameStateModel): _description_
            combos (List[Tuple[ActionModel,ActionModel,EquipmentModel]]): _description_

        Returns:
            List[ValidatedPlayActionModel]: _description_
        """
        # TODO: return type does not match yet
        playable_list = []
        actor = game_state.role
        asset_properties = ActorHelper.get_visible_asset_properties(game_state.assets_on_board)
        for main_action, support_action, equipment in combos:
            if support_action is None:
                support_actions = []
            else:
                support_actions = [support_action]
            if equipment is None:
                equipment = []
            else:
                equipment = [equipment]
            if main_action.predefined_attack_mask is not None and \
                main_action.predefined_attack_mask != EMPTY_ATTACK_MASK:
                possible_attack_masks = [main_action.predefined_attack_mask]
            else:
                possible_attack_masks = [C, I, A]
            
            for attack_mask in possible_attack_masks:
                validated_action = ValidatedPlayActionModel(
                    action=main_action,
                    support_actions=support_actions,
                    equipment=equipment,
                    attack_mask=attack_mask,
                )

                if main_action.card_type != CardType.MAIN:
                    # maybe raise an error in the future, because this should never 
                    # happen
                    continue

                def bot_options(config: ActionValidatorOptions):
                    config.bot_run = True
                    config.stop_on_error = True
                    config.skip_asset_checks = False
                ActionValidationHelper.validate_play(
                    game_state,
                    actor,
                    validated_action,
                    config=bot_options
                )
                # do not look for possible targets if the combination is not playable
                if not validated_action.is_playable():
                    playable_list.append(validated_action)
                    continue
                
                # find possible target assets for the main action
                if validated_action.action.target_type == TargetType.SINGLE:
                    possible_targets = ActionHelper.get_possible_targets(validated_action, asset_properties)
                    # no possible target for a single-targeted action restuls in an
                    # error message
                    if len(possible_targets) == 0:
                        validated_action.errors.append(
                            PenQuestException(
                                Errors.NoPlayableTargetAssetError,
                                f"There is currently no playable target asset for "
                                f"{validated_action.action.name}"
                            )
                        )
                        playable_list.append(validated_action)
                        continue
                    # check if support actions add some additional restrictions
                    for support_action in validated_action.support_actions:
                        support_possible_targets = ActionHelper.get_possible_targets_support_action(support_action, asset_properties)
                        possible_targets = set(possible_targets).intersection(support_possible_targets)
                    if len(possible_targets) == 0:
                        validated_action.errors.append(
                            PenQuestException(
                                Errors.NoPlayableTargetAssetError,
                                f"There is currently no playable target asset for "
                                f"{validated_action.action.name}"
                            )
                        )
                        playable_list.append(validated_action)
                        continue
                else:
                    if actor.is_attacker:
                        possible_targets = set(
                            [asset
                            for asset in game_state.assets_on_board
                            if not asset.is_offline
                            ]
                        )
                    else:
                        possible_targets = set(game_state.assets_on_board)
                validated_action.possible_targets = possible_targets

                # find possible response targets for a defense action
                if main_action.is_defense_action() and main_action.def_type == DefType.RESPONSE:
                    validated_action.possible_response_targets = dict()
                    for target_asset in possible_targets:
                        response_targets = GameHelper.get_possible_response_targets(
                            game_state,
                            validated_action.action,
                            target_asset,
                            validated_action.action.predefined_attack_mask
                        )
                        validated_action.possible_response_targets[target_asset.id] = response_targets
                        if len(response_targets) == 0:
                            validated_action.warnings.append(
                                PenQuestException(
                                    Errors.NoResponseTargetAvailable,
                                    f"There is currently no possible response target for "
                                    f"{validated_action.action.name} on asset {target_asset.name}"
                                )
                            )
                # add playable validated action
                playable_list.append(validated_action)
        
        # TODO: send request to server to get all success and detection chances
        # for all playable options
        return playable_list

    @staticmethod
    def get_validated_redraw_actions(
            game_state: GameStateModel,
        ) -> List[ValidatedRedrawActionModel]:
        """Fills in the field 'validated_actions' in the game state with a list
        of ValidatedRedrawActionModel objects, one object per action that is in
        the possible selection of the player and validates them.
        """
        validated_actions = []
        for action in game_state.selection_choices:
            validated_action = ValidatedRedrawActionModel(action=action)
            ActionValidationHelper.validate_redraw(
                game_state,
                game_state.role,
                validated_action
            )
            validated_actions.append(validated_action)
        return validated_actions

    @staticmethod
    def get_validated_play_actions(
            game_state: GameStateModel
        ) -> List[ValidatedPlayActionModel]:
        """Retrieves a list of all 3-way combinations of main action, support
        action and equipment the player has on its hand and determines whether
        this combination is currently playable. If it is playable it also
        returns a list of possible target assets and a dictionary of possible
        response action targets.

        :return: list of all valid actions
        """

        # get all combinations of main action, support action and equipment
        all_action_combinations = GameHelper.get_all_action_combs(game_state)
        
        # validate all combinations from above and for valid combinations, find
        # possible target assets, attack mask and response target actions.
        valid_actions = GameHelper.get_valid_play_action_combs(
            game_state,
            all_action_combinations
        )
        return valid_actions

    @staticmethod
    def get_idx_actions(
            validated_actions: List[ValidatedPlayActionModel],
            game_state: GameStateModel,
        ) -> List[Tuple[int, int, int, int, int, int]]:
        """Translates a list of ValidatedPlayActionModels into a list of 6-way
        tuples of integers where each integer indicates an action, equpment,
        attack mask or asset in order to play an action.

        Args:
            game_state (GameStateModel): current state of the game
            validated_actions (List[ValidatedPlayActionModel]): list of validated
                action combinations    

        Returns:
            List[Tuple[int, int, int, int, int, int]]: list of integer
                tuples where each tuple indicates a single action that can be
        """
        comb_generators = []
        for validated_action in validated_actions:
            if not validated_action.is_playable():
                continue
            main_action_idx = game_state.hand.index(validated_action.action)
            # The option of having no support action is 0 therefore all
            # indices of support actions are shifted +1.
            if len(validated_action.support_actions) == 0:
                supp_action_idx = 0
            else:
                # currently it is only allowed to select one support action
                # anyway, therefore always choose the first one.
                supp_action_idx = game_state.hand.index(validated_action.support_actions[0])+1
            # The option of having no equipment is 0 therefore all
            # indices of equipment are shifted +1.
            if len(validated_action.equipment) == 0:
                equipment_idx = 0
            else:
                # currently it is only allowed to select one support action
                # anyway, therefore always choose the first one
                equipment_idx = game_state.equipment.index(validated_action.equipment[0])+1
            attack_mask_idx = VALID_ATTACK_MASKS.index(validated_action.attack_mask)
            if len(validated_action.possible_targets) == 0:
                comb_generators.append(
                    itertools.chain.from_iterable(
                        [
                            itertools.product(
                                [main_action_idx],
                                [0],
                                [attack_mask_idx],
                                [supp_action_idx],
                                [equipment_idx],
                                [0]
                            )
                        ]
                    )
                )
            else:
                for target_asset in validated_action.possible_targets:
                    if len(validated_action.possible_response_targets) == 0:
                        response_targets = [0]
                    else:
                        response_targets = [action.id for action in validated_action.possible_response_targets[target_asset.id]]
                        if len(response_targets) == 0:
                            response_targets = [0]
                    comb_generators.append(
                        itertools.chain.from_iterable(
                            [
                                itertools.product(
                                    [main_action_idx],
                                    [target_asset.id],
                                    [attack_mask_idx],
                                    [supp_action_idx],
                                    [equipment_idx],
                                    response_targets
                                )
                            ]
                        )
                    )
        valid_actions = tuple(itertools.chain.from_iterable(comb_generators))
        return valid_actions

    @staticmethod
    def get_valid_actions(
            game_state: GameStateModel
        ) -> List[Tuple[int, int, int, int, int, int]]:
        """Retrieves a list of 6-way tuples of integers where each integer
        indicates an action, equpment, attack mask or asset in order to play
        an action. 

        Args:
            game_state (GameStateModel): current state of the game

        Returns:
            List[Tuple[int, int, int, int, int, int]]: list of integer tuples
                where each tuple indicates a single action that can be executed
                by an agent/bot. The integers of the tuple have the following 
                meaning:
                    position 0 - index (of actions in hand) of the main action.
                        Index starts with 0 (as usual). 
                    position 1 - index (of actions in hand) of a support action
                        shifted by +1. 0 inidcates that no support action is 
                        provided.
                    position 2 - index (of equipment in hand) of an equipment
                        shifted by +1. 0 inidcates that no equipment is 
                        provided.
                    position 3 - index (of valid attack masks) of the provided
                        attack mask. 
                    position 4 - id of the target asset the main action is
                        played on
                    position 5 - id of the response target action on the target
                        asset
        """
        valid_actions = []
        
        if game_state.validated_actions is None or len(game_state.validated_actions) == 0:
            validated_actions = GameHelper.get_validated_play_actions(game_state)
        else:
            validated_actions = game_state.validated_actions
        valid_actions = GameHelper.get_idx_actions(validated_actions, game_state)
        return valid_actions

    @staticmethod
    def is_any_validated_action_playable(game_state: GameStateModel) -> bool:
        """Checks if any of the validated actions is currently playable. If not
        or if there are no validated actions, returns False.

        Args:
            game_state (GameStateModel): current state of the game

        Returns:
            bool: indicates if there is currently any playable action
        """
        if game_state.validated_actions is None or len(game_state.validated_actions) == 0:
            return False

        for validated_action in game_state.validated_actions:
            if validated_action.is_playable():
                return True

    @staticmethod
    def get_playable_action_combs(game_state: GameStateModel) -> List[ValidatedPlayActionModel]:
        """Reads the 'validated_actions' property of the game state and filters
        it for only those that are currently playable. Returns a list of

        Args:
            game_state (GameStateModel): current state of the game

        Returns:
            List[ValidatedPlayActionModel]: list of validated action combinations that
                are currently playable
        """
        if game_state.validated_actions is None or len(game_state.validated_actions) == 0:
            return []
        
        playable_actions = [
            validated_action 
            for validated_action in game_state.validated_actions
            if validated_action.is_playable()
        ]
        return playable_actions

    @staticmethod
    def get_asset_from_board(game_state: GameStateModel, asset_id: int) -> AssetModel:
        """Returns the asset with the provided id from the board"""
        # TODO: write unittests for this method
        asset = next(
                (a for a in game_state.assets_on_board if a.id == asset_id),
                None
        )
        return asset

    @staticmethod
    def get_integrity_assets(game_state: GameStateModel) -> List[AssetModel]:
        """Returns a list of assets that do not yet have full integrity damage"""
        return [asset for asset in game_state.assets_on_board if asset.damage.I < 3]

    @staticmethod
    def get_most_attack_stage(game_state: GameStateModel) -> int:
        """Returns the highest attack stage of all assets on the board"""
        return max([asset.attack_stage for asset in game_state.assets_on_board])
    
    @staticmethod
    def get_damaged_assets(game_state: GameStateModel) -> List[AssetModel]:
        """Returns a list of assets that have taken damage"""
        return [asset for asset in game_state.assets_on_board if asset.is_damaged()]
