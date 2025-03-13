from typing import Callable
from penquest_pkgs.game.action_validator import (
    ActionValidator,
    ActionValidatorOptions,
)
from penquest_pkgs.model import  (
    ActorModel,
    EquipmentModel,
    AssetModel,
    ActionModel,
    GameStateModel,
    ValidatedPlayActionModel,
    ValidatedRedrawActionModel,
)
from penquest_pkgs.constants import (
    GamePhase,
    TargetType,
    CardType,
    ActorType,
    GameInteractionPhase,
    EquipmentShopMode,
    EffectType,
)
from penquest_pkgs.exceptions import Errors, PenQuestException
from penquest_pkgs.game.actor_helper import ActorHelper
from penquest_pkgs.game.asset_helper import AssetHelper


class ActionValidationHelper():

    playing_validator = ActionValidator()
    redraw_validator = ActionValidator()
    client_validator = ActionValidator()

    

    def __new__(cls, *args, **kwargs):
        raise TypeError("This is a static class and cannot be instantiated")

    @classmethod
    def validate_play(
        cls,
        game_state: GameStateModel,
        actor: ActorModel,
        validated_action: ValidatedPlayActionModel,
        config: Callable[[ActionValidatorOptions], None] = None,
        client: bool = False
    ) -> ValidatedPlayActionModel:
        """Validates an action-support_action-equipment tripled according to
        the current game state.

        Args:
            game_state (GameStateModel): the current game state
            actor (ActorModel): the actor object of the player that is
                performing the action
            validated_action (ValidatedPlayActionModel): the object that stores all the
                information about the validation check
            config (Callable[[ActionValidatorOptions], None], optional): 
                Optional configs for the validation. Defaults to None.
            client (bool, optional): a flag whether the client checks
                that made sense on the server should also be checked. 
                This option might be obsolete in the future.Defaults to False.

        Returns:
            ValidatedPlayActionModel: the same validated action object that was passed
                as an argument but now with more information (errors if any
                check was violated)
        """
        cls.playing_validator.validate(
            game_state,
            actor,
            validated_action,
            config=config
        )
        # invokes checks that made sense on the server, meaning that the client
        # would not cheat the server. However since these checks are no on the 
        # client, they don't make a whole lot of sense anymore.
        if client:
            cls.client_validator.validate(
                game_state,
                actor,
                validated_action,
                config=config
            )
        return validated_action

    @classmethod
    def validate_redraw(
        cls,
        game_state: GameStateModel,
        actor: ActorModel,
        validated_action: ValidatedPlayActionModel,
        config: Callable[[ActionValidatorOptions], None] = None,
    ) -> ValidatedPlayActionModel:
        """Validates a single action on whether it could be currently played
        the current game state.

        Args:
            game_state (GameStateModel): the current game state
            actor (ActorModel): the actor object of the player that is
                performing the action
            validated_action (ValidatedPlayActionModel): the object that stores all the
                information about the validation check
            config (Callable[[ActionValidatorOptions], None], optional): 
                Optional configs for the validation. Defaults to None.
            client (bool, optional): a flag whether the client checks
                that made sense on the server should also be checked. 
                This option might be obsolete in the future.Defaults to False.

        Returns:
            ValidatedPlayActionModel: the same validated action object that was passed
                as an argument but now with more information (errors if any
                check was violated)
        """
        cls.redraw_validator.validate(
            game_state,
            actor,
            validated_action,
            config=config
        )
        return validated_action

    @classmethod
    def _init(cls):
        cls.setup_play_checks()
        cls.setup_redraw_checks()
        cls.setup_client_checks()
    
    @classmethod
    def setup_play_checks(cls):

        # Check for validitiy between the combination of main action, support
        # action and equipment
        # Check if support actions match the main action
        def validate_support_actions(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Checks if provided support actions are indeed support actions and if they are compatible
            the main action

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """

            main_action = validated_action.action
            support_actions = validated_action.support_actions
            for support_action in support_actions:
                if support_action.card_type != CardType.SUPPORT:
                    validated_action.errors.append(
                        PenQuestException(
                            Errors.NotASupportActionError,
                            f"Action '{support_action.name}({support_action.template_id})' is not a support action"
                        )
                    )
                if len(support_action.possible_actions) > 0 and main_action.template_id not in support_action.possible_actions:
                    validated_action.errors.append(
                        PenQuestException(
                            Errors.SupportActionMainActionMismatchError,
                            f"Support action '{support_action.name}({support_action.template_id})' is incompatible with main action '{main_action.name}({main_action.template_id})'"
                        )
                    )
        cls.playing_validator.add_validation(validate_support_actions)

         # Check if the equipment match the main action
        def validate_equipment_compatible(
                game_state: GameStateModel,
                actor: ActorModel,
                equipment: EquipmentModel,
                validated_action: ValidatedPlayActionModel
            ):
            """Checks that attached equipment is compatible with the main action

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                equipment (EquipmentModel): equipment that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            main_action = validated_action.action
            required_equipment_ids = [eq.id for eq in main_action.required_equipment]
            # skip check if equipment is required for the action => assume it's on the list
            if equipment.template_id in required_equipment_ids:
                return
            
            # it no possible_actions are provided, then all are applicable
            if len(equipment.possible_actions) > 0 and not main_action.template_id in equipment.possible_actions:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.EquipmentMainActionMismatchError,
                        f"Equipment '{equipment.name}({equipment.template_id})' is incompatible with action '{main_action.name}({main_action.template_id})'"
                    )
                )
        cls.playing_validator.add_equipment_validation(validate_equipment_compatible)

        # Check if required equipment is in the possession of the actor
        def validate_required_equipment(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that all required equipment for the main action was bought by the actor

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            # only check required equipment if shop is enabled
            if game_state.game_options.equipment_shop_mode == EquipmentShopMode.DISABLED:
                return
            
            required_equipment_ids = [eq.id for eq in validated_action.action.required_equipment]
            for support_action in validated_action.support_actions:
                required_equipment_ids += [eq.id for eq in support_action.required_equipment]

            # only check if there are required equipment
            if len(required_equipment_ids) == 0:
                return
            
            found = False
            for req_eq_id in required_equipment_ids:
                # TODO: check if equipment is in general present in the game
                if req_eq_id in [eq.template_id for eq in validated_action.equipment]:
                    found = True
                    break
                elif req_eq_id in [eq.template_id for eq in actor.equipment if eq.is_passive_equipment]:
                    found = True
                    break
            if not found:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.ActionRequiredEquipmentMissing,
                        f"Missing required equipment for action '{validated_action.action.name}({validated_action.action.template_id})'"
                    )
                )
        cls.playing_validator.add_validation(validate_required_equipment)

        # Check if local equipment is attached to a multi-targeted action
        def validate_local_equipment(
                game_state: GameStateModel,
                actor: ActorModel,
                equipment: EquipmentModel,
                validated_action: ValidatedPlayActionModel
            ):
            """Checks if a local equipment is attached to a multi-targeted action

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                equipment (EquipmentModel): equipment that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            if equipment.is_local_equipment and validated_action.action.target_type == TargetType.MULTI:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.NoLocalEquipmentOnMultitargetAction,
                        f"Local equipment '{equipment.name}({equipment.template_id})' cannot be appended to a multi-target action"
                    )
                )   
        cls.playing_validator.add_equipment_validation(validate_local_equipment)

        # Check if no passive equipment is attached
        def validate_passive_equipment(
                game_state: GameStateModel,
                actor: ActorModel,
                equipment: EquipmentModel,
                validated_action: ValidatedPlayActionModel
            ):
            """Checks that no passive equipment is attached

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                equipment (EquipmentModel): equipment that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            if equipment.is_passive_equipment:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.WrongEquipmentType,
                        f"Passive equipment '{equipment.name}({equipment.template_id})' cannot be appended to an action"
                    )
                )  
        cls.playing_validator.add_equipment_validation(validate_passive_equipment)

        # Checks for the validity between the combination and the current game
        # state
        # Check if the actor has enough action points to play the action
        def validate_action_points(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            if game_state.game_phase == GamePhase.DefenderPreSetup:
                return
            total_aps = validated_action.get_total_action_point_costs()
            min_aps = ActorHelper.get_min_aps(game_state.role)
            if game_state.action_points - total_aps < min_aps:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.MissingActionError,
                        f"Actor only has {game_state.action_points} action "
                        f"points left, but needs action requires {total_aps} "
                        "action points to play"
                    )
                )
        cls.playing_validator.add_validation(validate_action_points)

        # Checks for the validity between the combination and the role of the
        # player
        # Check if the actor has enough soph to play the action
        def validate_main_action_soph_req(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that the actor has the required SOPH to play the main action

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            main_action = validated_action.action
            if actor.soph < main_action.soph_requirement:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.MissingSophError,
                        f"Actor has not enough SOQH to play action '{main_action.name}({main_action.template_id})'"
                    )
                )
        cls.playing_validator.add_validation(validate_main_action_soph_req)

        # Check if the actor has enough soph to play the support actions
        def validate_support_actions_soph_req(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that the actor has the required SOPH to play the support actions

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            for support_action in validated_action.support_actions:
                if actor.soph < support_action.soph_requirement:
                    validated_action.errors.append(
                        PenQuestException(
                            Errors.MissingSophError,
                            f"Actor has not enough SOQH to play support action '{support_action.name}({support_action.template_id})'"
                        )
                    )
        cls.playing_validator.add_validation(validate_support_actions_soph_req)

        # Check for the validity between the combination and the possible target
        # asset(s)
        # TODO: these checks are probably unncessary, because the assets are not
        # yet matched to the validated action
        # Check if the target asset is online
        def validate_asset_is_online(game_state: GameStateModel, actor: ActorModel, asset: AssetModel, validated_action: ValidatedPlayActionModel):
            """Validates that the target asset is online

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            if validated_action.action.is_attack_action() and not asset.is_online:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.AssetOfflineError,
                        f"Target asset '{asset.name}' is currently not reachable/offline"
                    )
                )
        cls.playing_validator.add_asset_validation(validate_asset_is_online)

        def validate_attack_mask_exposed(game_state: GameStateModel, actor: ActorModel, asset: AssetModel, validated_action: ValidatedPlayActionModel):
            """Validates that the asset is exposed at the provided attack mask

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            if validated_action.action.is_attack_action() and asset.is_attack_vector_partially_available(validated_action.attack_mask):
                validated_action.errors.append(
                    PenQuestException(
                        Errors.AssetNotExposedError,
                        f"Asset '{asset.name}' is not exposed at attack mask '{validated_action.attack_mask}'"
                    )
                )
        cls.playing_validator.add_asset_validation(validate_attack_mask_exposed)

        def validate_defense_action_checks(game_state: GameStateModel, actor: ActorModel, asset: AssetModel, validated_action: ValidatedPlayActionModel):
            """Validates that the asset is exposed at the provided attack mask

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            main_action = validated_action.action
            if not main_action.is_defense_action():
                return
            
            if validated_action.response_target_id == 0:
                return 
            
            if not any([action.id == validated_action.response_target_id for action in asset.played_actions]):
                validated_action.errors.append(
                    PenQuestException(
                        Errors.InvalidResponseTarget,
                        f"Target {validated_action.response_target_id} does not correspond to any played action of asset '{asset.name}'"
                    )
                )
            
            response_target_action = next(action for action in asset.played_actions if action.id == validated_action.response_target_id)
            response_target_action_event = next(event for event in response_target_action.events if event.asset_id == asset.id)

            if response_target_action_event is None:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.IndexErrorFatal,
                        f"Asset '{asset.name}' has no event for action '{response_target_action.name}({response_target_action.template_id})'"
                    )
                )
            
            if not response_target_action_event.succeeded:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.InvalidResponseTarget,
                        f"Target action '{response_target_action.name}({response_target_action.template_id})' corresponds to an unsuccessful action on asset '{asset.name}'"
                    )
                )
            
            # Check for detected is irrelevant for the client because if it 
            # hadn't detected the action (event) it couldn't respond to it 
            # anyway.

            # Chekf for (b2) is unclear to me, but it seems to me it is a sanity
            # check for the server, so not relevant for the client

            if response_target_action_event.attack_mask_used is None:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.InvalidResponseTarget,
                        f"Target action '{response_target_action.name}"
                        f"({response_target_action.template_id})' does not "
                        f"correspond to a valid played action on asset "
                        f"{asset.name} (b3)"
                    )
                )

            if response_target_action_event.asset_id is not None and \
                not response_target_action_event.is_currently_counterable(game_state):
                validated_action.errors.append(
                    PenQuestException(
                        Errors.InvalidResponseTarget,
                        f"Target action '{response_target_action.name}"
                        f"({response_target_action.template_id})' does not "
                        f"correspond to a valid played action on asset "
                        f"{asset.name} (b4)"
                    )
                )
        cls.playing_validator.add_asset_validation(validate_defense_action_checks)

        def validate_oses(
                game_state: GameStateModel, 
                actor: ActorModel, 
                asset: AssetModel,
                action: ActionModel, 
                validated_action: ValidatedPlayActionModel
            ):
            """Validates that the OS of the action is compatible with the OS
            of the asset

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is 
                    being checked
            """
            if not asset.os not in action.oses:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.OsMismatchError,
                        f"Action '{action.name}({action.template_id})' is not "
                        f"playable on OS '{asset.os}'"
                    )
                )
        cls.playing_validator.add_action_validation(validate_oses)

        def validate_asset_category(
                game_state: GameStateModel,
                actor: ActorModel,
                asset: AssetModel,
                action: ActionModel,
                validated_action: ValidatedPlayActionModel
            ):
            """Validates that the action is compatible with the asset category

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is 
                    being checked
            """
            if not asset.category in action.asset_categories:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.ActionAssetMismatchError,
                        f"Action '{action.name}({action.template_id})' is not "
                        f"playable on asset '{asset.category}'"
                    )
                )
            if len(validated_action.equipment) > 0:
                for eq in validated_action.equipment:
                    if not asset.category in eq.possible_asset_categories:
                        validated_action.errors.append(
                            PenQuestException(
                                Errors.EquipmentAssetCategoryMismatchError,
                                f"Equipment '{eq.name}({eq.template_id})' is not "
                                f"playable on asset '{asset.category}'"
                            )
                        )
        cls.playing_validator.add_action_validation(validate_asset_category)

        def validate_equipment_category(
                game_state: GameStateModel, 
                actor: ActorModel, 
                equipment: EquipmentModel,
                asset: AssetModel,
                validated_action: ValidatedPlayActionModel
            ):
            """Validates that the equipment ist compatible with the asset 
            category

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is 
                    being checked
            """
            if not equipment.is_compatible_with(asset.category):
                validated_action.errors.append(
                    PenQuestException(
                        Errors.EquipmentAssetIdMismatchError,
                        f"Equipment '{equipment.name}({equipment.template_id})' is not "
                        f"compatible with asset '{asset.category}'"
                    )
                )
        cls.playing_validator.add_equipment_asset_validation(validate_equipment_category)

        def validate_equipment_asset_id(
                game_state: GameStateModel, 
                actor: ActorModel, 
                equipment: EquipmentModel,
                asset: AssetModel,
                validated_action: ValidatedPlayActionModel
            ):
            """Validates that the equipment is compatible with the asset id

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is 
                    being checked
            """
            if not equipment.is_compatible_with_asset_id(asset.id):
                validated_action.errors.append(
                    PenQuestException(
                        Errors.EquipmentAssetIdMismatchError,
                        f"Equipment '{equipment.name}({equipment.template_id})'"
                        f" is not compatible with asset '{asset.category}'"
                    )
                )
        cls.playing_validator.add_equipment_asset_validation(validate_equipment_asset_id)

        def validate_attack_stages(
                game_state: GameStateModel, 
                actor: ActorModel, 
                asset: AssetModel,
                action: ActionModel, 
                validated_action: ValidatedPlayActionModel
            ):
            """Validates that the action can be played at the current attack stage

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is 
                    being checked
            """
            if asset.attack_stage < action.attack_stage:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.AttackStageMismatchError,
                        f"Action '{action.name}({action.template_id})' is not "
                        f"playable at attack stage '{asset.attack_stage}'"
                    )
                )
        cls.playing_validator.add_action_validation(validate_attack_stages)

        def validate_admin_priviledges(
                game_state: GameStateModel, 
                actor: ActorModel, 
                asset: AssetModel,
                action: ActionModel, 
                validated_action: ValidatedPlayActionModel
            ):
            """Validates that the actor has admin rights if necessary

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is 
                    being checked
            """
            if action.requires_admin and not asset.has_admin_rights:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.AdminModeRequired,
                        f"Action '{action.name}({action.template_id})' requires "
                        f"admin priviledges"
                    )
                )
        cls.playing_validator.add_action_validation(validate_admin_priviledges)

        # Check for the validity between the combination and conditions of
        # effects.
        # Check if the actor has enough credits to play the action
        def validate_effect_conditions(
                game_state: GameStateModel, 
                actor: ActorModel, 
                validated_action: ValidatedPlayActionModel
            ):
            """Validates that the conditions for the effects are met

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                asset (AssetModel): target asset that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is 
                    being checked
            """
            main_action = validated_action.action
            support_actions = validated_action.support_actions
            equipment = validated_action.equipment

            # gather all effects from actions and equipment
            effects = main_action.effects
            for support_action in support_actions:
                effects += support_action.effects
            for eq in equipment:
                effects += eq.effects

            for effect in effects:
                if effect.type == EffectType.MODIFY_ACTOR and "credits" in effect.attributes and effect.value is not None:
                    if main_action.target_type in [TargetType.SINGLE, TargetType.UNTARGETED]:
                        if actor.credits + effect.value < 0:
                            validated_action.errors.append(
                                PenQuestException(
                                    Errors.NotEnoughCreditsError,
                                    f"Not enough credits to play action "
                                    f"'{main_action.name}({main_action.template_id})'"
                                )
                            )
                    elif main_action.target_type == TargetType.MULTI:
                        amount_assets = max(
                            len(actor.visible_assets),
                            len(actor.assets)
                        )
                        if actor.credits + effect.value*amount_assets < 0:
                            validated_action.errors.append(
                                PenQuestException(
                                    Errors.NotEnoughCreditsError,
                                    f"Not enough credits to play action "
                                    f"'{main_action.name}({main_action.template_id})'"
                                )
                            )
                    else:
                        # this should never happen
                        raise PenQuestException(
                            Errors.TypeErrorFatal,
                            f"Unknown target type '{main_action.target_type}'"
                        )
        cls.playing_validator.add_validation(validate_effect_conditions)

    @classmethod
    def setup_redraw_checks(cls):

        # First validate that the actor can play the action with actor attributes
        # Validate Soph
        def validate_redraw_soph(
                game_state: GameStateModel,
                actor: ActorModel,
                validated_action: ValidatedRedrawActionModel,
            ):
            if actor.soph < validated_action.action.soph_requirement:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.MissingSophError,
                        "Actor has not sufficient soph for the action"
                    )
                )
        cls.redraw_validator.add_validation(validate_redraw_soph)

        # Validate action points
        def validate_redraw_action_points(
                game_state: GameStateModel,
                actor: ActorModel,
                validated_action: ValidatedRedrawActionModel
            ):
            if game_state.action_points - validated_action.get_total_action_point_costs() < ActorHelper.get_min_aps(game_state.role):
                validated_action.errors.append(
                    PenQuestException(
                        Errors.InsufficientActionPointsError,
                        "Actor has not sufficient action points for the action"
                    )
                )
        cls.redraw_validator.add_validation(validate_redraw_action_points)

        # Validate if the actor has enough credits to play the action,
        # currently only effects of an action require credits
        def validate_redraw_effect_conditions(
                game_state: GameStateModel,
                actor: ActorModel,
                validated_action: ValidatedRedrawActionModel
            ):
            for effect in validated_action.action.effects:
                if effect.type == EffectType.MODIFY_ACTOR and "credits" in effect.attributes and effect.value is not None:
                    if actor.credits + effect.value < 0:
                        validated_action.errors.append(
                            PenQuestException(
                                Errors.NotEnoughCreditsError,
                                f"Not enough credits to play action "
                                f"'{validated_action.action.name}"
                                f"({validated_action.action.id})'"
                            )
                        )
        cls.redraw_validator.add_validation(validate_redraw_effect_conditions)

        # Check if the actor already posses required equipment
        def validate_redraw_required_equipment(
                game_state: GameStateModel,
                actor: ActorModel,
                validated_action: ValidatedRedrawActionModel
            ):
            # only check required equipment if shop is enabled
            if game_state.game_options.equipment_shop_mode == EquipmentShopMode.DISABLED:
                return
            
            required_equipment_ids = set(
                [
                    eq.id 
                    for eq in validated_action.action.required_equipment
                ]
            )

            # only check if there are required equipment
            if len(required_equipment_ids) == 0:
                return
            
            found = False
            purchased_eq_ids = set(eq.id for eq in actor.equipment)
            intersect = required_equipment_ids.intersection(purchased_eq_ids)
            if len(intersect) == 0:
                validated_action.errors.append(
                        PenQuestException(
                            Errors.ActionRequiredEquipmentMissing,
                            f"Missing required equipment for action "
                            f"'{validated_action.action.name}"
                            f"({validated_action.action.id})'"
                        )
                    )
        cls.redraw_validator.add_validation(validate_redraw_required_equipment)

        # Check if the actors has any asset that the action can be played on to
        def validate_redraw_has_target_asset(
                game_state: GameStateModel,
                actor: ActorModel,
                validated_action: ValidatedRedrawActionModel
            ):
            if validated_action.action.target_type == TargetType.SINGLE:
                found_asset = False
                for asset in game_state.assets_on_board:
                    if AssetHelper.is_action_playable_on_asset(validated_action.action, asset):
                        found_asset = True
                        break
                if not found_asset:
                    validated_action.errors.append(
                        PenQuestException(
                            Errors.MissingAssetError,
                            f"No valid target asset for action "
                            f"'{validated_action.action.name}"
                            f"({validated_action.action.id})' was found"
                        )
                    )
        cls.redraw_validator.add_validation(validate_redraw_has_target_asset)

        # Check if the action is a support action, whether the actor has a
        # compatible main action the support action can support
        def validate_redraw_support_action(
                game_state: GameStateModel,
                actor: ActorModel,
                validated_action: ValidatedRedrawActionModel
            ):
            if validated_action.action.card_type != CardType.SUPPORT:
                return
            found_main_action = False
            for action in game_state.hand:
                if action.card_type != CardType.MAIN:
                    continue
                if action.id in validated_action.action.possible_actions:
                    found_main_action = True
                    break
            if not found_main_action:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.SupportActionMainActionMismatchError,
                        f"No valid main action for support action "
                        f"'{validated_action.action.name}"
                        f"({validated_action.action.id})' was found"
                    )
                )
        cls.redraw_validator.add_validation(validate_redraw_support_action)

    @classmethod
    def setup_client_checks(cls):
        # check for client
        def validate_main_action(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Checks if provided action is indeed a main action

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """

            main_action = validated_action.action
            if main_action.card_type != CardType.MAIN:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.NotAMainActionError,
                        f"Action '{main_action.name}({main_action.template_id})' is not a main action"
                    )
                )
        cls.client_validator.add_validation(validate_main_action)

        # check for client
        def validate_equipment_not_used(
                game_state: GameStateModel,
                actor: ActorModel,
                equipment: EquipmentModel,
                validated_action: ValidatedPlayActionModel
            ):
            """Checks that attached equipment is not used twice

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                equipment (EquipmentModel): equipment that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            if equipment.is_local_equipment and equipment.is_used and not equipment.is_reusable:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.EquipmentAlreadyUsed,
                        f"Equipment '{equipment.name}({equipment.template_id})' is already used"
                    )
                )  
        cls.client_validator.add_equipment_validation(validate_equipment_not_used)

         # check for client
        def validate_role_type_attack(
                game_state: GameStateModel,
                actor: ActorModel,
                validated_action: ValidatedPlayActionModel
            ):
            """Checks that all support actions and equipment are of attack type if main
            action is an attack action.

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                equipment (EquipmentModel): equipment that is being checked
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            main_action = validated_action.action
            support_actions = validated_action.support_actions
            equipment = validated_action.equipment

            if main_action.is_attack_action():
                for support_action in support_actions:
                    if not support_action.is_attack_action():
                        validated_action.errors.append(
                            PenQuestException(
                                Errors.SupportActionMainActionMismatchError,
                                f"Support action '{support_action.name}({support_action.template_id})' is not of type attack"
                            )
                        )
                for eq in equipment:
                    if not eq.is_attack_equipment:
                        validated_action.errors.append(
                            PenQuestException(
                                Errors.EquipmentMainActionMismatchError,
                                f"Equipment '{eq.name}({eq.template_id})' is not of type attack"
                            )
                        )
        cls.client_validator.add_validation(validate_role_type_attack)

        # check for client
        def validate_role_type_defense(
                game_state: GameStateModel, 
                actor: ActorModel, 
                validated_action: ValidatedPlayActionModel
            ):
            """Checks that all support actions and equipment are of defense type if main
            action is a defense action.

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            main_action = validated_action.action
            support_actions = validated_action.support_actions
            equipment = validated_action.equipment

            if main_action.is_defense_action():
                for support_action in support_actions:
                    if not support_action.is_defense_action():
                        validated_action.errors.append(
                            PenQuestException(
                                Errors.SupportActionMainActionMismatchError,
                                f"Support action '{support_action.name}({support_action.template_id})' is not of type defense"
                            )
                        )
                for eq in equipment:
                    if not eq.is_defense_equipment:
                        validated_action.errors.append(
                            PenQuestException(
                                Errors.EquipmentMainActionMismatchError,
                                f"Equipment '{eq.name}({eq.template_id})' is not of type defense"
                            )
                        )
        cls.client_validator.add_validation(validate_role_type_defense)

        # check for client
        def validate_game_phase(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that eh game is in the correct game phase for the action

            Args:
                game (Game): _description_
                actor (ActorModel): _description_
                validated_action (ValidatedPlayActionModel): _description_
            """
            if actor.type == ActorType.ATTACK:
                expected_game_phase = GamePhase.Attacker
            elif actor.type == ActorType.DEFENCE:
                expected_game_phase = GamePhase.Defender
            else:
                # this should never happen
                raise PenQuestException(
                    Errors.UnknownActorError,
                    f"Actor {actor} is of unknown type '{actor.type}'"
                )
            if game_state.game_phase != expected_game_phase:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.InvalidGamePhase,
                        f"Wrong game phase. Game phase is '{game_state.game_phase}' but expected '{expected_game_phase}'"
                    )
                )
        cls.client_validator.add_validation(validate_game_phase)

        # check for client
        def validate_not_yet_played(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that the action has not been played yet

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            if len(validated_action.action.events) > 0:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.ActionAlreadyPlayedError,
                        f"Action '{validated_action.action.name}({validated_action.action.template_id})' has already been played"
                    )
                )
        cls.client_validator.add_validation(validate_not_yet_played)

        # check for client
        def validate_has_finished(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that the actor has not yet finished playing acitons in this turn

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            if game_state.interaction_phase != GameInteractionPhase.Playing:
                raise PenQuestException(
                    Errors.ActorPhaseAlreadyCompletedError,
                    f"Invalid interaction phase '{game_state.interaction_phase}'"
                )
        cls.client_validator.add_validation(validate_has_finished)

        # check for client
        def validate_support_actions_exist(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that the actor has the support actions on its hand and hasn't played them yet

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            action_ids = [sa.id for sa in actor.actions]
            for support_action in validated_action.support_actions:
                if support_action.id not in action_ids:
                    validated_action.errors.append(
                        PenQuestException(
                            Errors.ActionNotInPossessionError,
                            f"Support action '{support_action.name}({support_action.template_id})' is not in your posession. Don't try to cheat me!"
                        )
                    )
                if support_action.is_used:
                    validated_action.errors.append(
                        PenQuestException(
                            Errors.ActionAlreadyPlayedError,
                            f"Support action '{support_action.name}({support_action.template_id})' has already been played"
                        )
                    )
        cls.client_validator.add_validation(validate_support_actions_exist)

        # check for client
        def validate_equipment_exists(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that the actor has the equipment on its hand and hasn't played them yet

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            equipment_ids = [eq.id for eq in actor.equipment]
            for equipment in validated_action.equipment:
                if equipment.id not in equipment_ids:
                    validated_action.errors.append(
                        PenQuestException(
                            Errors.EquipmentNotInPossessionError,
                            f"Equipment '{equipment.name}({equipment.template_id})' is not in your posession. Don't try to cheat me!"
                        )
                    )
        cls.client_validator.add_validation(validate_equipment_exists)

        # check for client
        def validate_main_action_exists(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that the actor has the main action on its hand and hasn't played it yet

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            action_ids = [a.id for a in actor.actions]
            if validated_action.action.id not in action_ids:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.ActionNotInPossessionError,
                        f"Main action '{validated_action.action.name}({validated_action.action.template_id})' is not in your posession. Don't try to cheat me!"
                    )
                )
        cls.client_validator.add_validation(validate_main_action_exists)

        # check for client
        def validate_actor_type_attacker(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that the actor is of type attacker

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            main_action = validated_action.action
            if main_action.is_attack_action() and actor.type != ActorType.ATTACK:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.ActionActorMismatchError,
                        f"Action '{main_action.name}({main_action.template_id})' is an attack action but actor is of type '{actor.type}'"
                    )
                )
        cls.client_validator.add_validation(validate_actor_type_attacker)

        # check for client
        def validate_actor_type_defender(game_state: GameStateModel, actor: ActorModel, validated_action: ValidatedPlayActionModel):
            """Validates that the actor is of type defender

            Args:
                game (Game): object that contains all information about a game
                actor (ActorModel): actor that is performing the action
                validated_action (ValidatedPlayActionModel): validated action that is being checked
            """
            main_action = validated_action.action
            if main_action.is_defense_action() and actor.type != ActorType.DEFENCE:
                validated_action.errors.append(
                    PenQuestException(
                        Errors.ActionActorMismatchError,
                        f"Action '{main_action.name}({main_action.template_id})' is a defense action but actor is of type '{actor.type}'"
                    )
                )
        cls.client_validator.add_validation(validate_actor_type_defender)


ActionValidationHelper._init()