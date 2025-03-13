from penquest_pkgs.network.game_messages.message_models import (
    PlayerMessageModel,
    GameOptionsMessageModel,
    GameOptionLocksMessageModel,
    SlotInfoMessageModel,
    ScenarioTeaserMessageModel,
    GoalDescMessageModel,
    LobbyMessageModel,
    EffectMessageModel,
    EquipmentTemplateMessageModel,
    EquipmentMessageModel,
    ActionEventMessageModel,
    ActionTemplateMessageModel,
    ActionMessageModel,
    AssetMessageModel,
    GoalMessageModel,
    ActorMessageModel,
    GameMessageModel,
    ErrorsMessageModel,
    ActionChanceModifierMessageModel,
    AssetChangesMessageModel,
    PostGameSummaryMessageModel,
    EventEntryMessageModel,
    SelectedActionMessageModel,
)

from penquest_pkgs.model import (
    PlayerModel,
    GameOptionsModel,
    GameOptionLocksModel,
    SlotInfoModel,
    ScenarioTeaserModel,
    GoalDescModel,
    LobbyModel,
    DamageModel,
    EffectModel,
    EquipmentTemplateModel,
    EquipmentModel,
    ActionEventModel,
    ActionTemplateModel,
    ActionModel,
    ExposedModel,
    AssetModel,
    GoalModel,
    ActorModel,
    GameModel,
    ErrorsModel,
    ActionChanceModifierModel,
    AssetChangesModel,
    PostGameSummaryModel,
    EventEntryModel,
    SelectedActionModel,
)

class PlayerMapper():

    @classmethod
    def map(cls, player_message_model: PlayerMessageModel) -> PlayerModel:
        player = PlayerModel(
            id=player_message_model.id,
            connection_id=player_message_model.connection_id,
            name=player_message_model.name,
            online=player_message_model.online,
            user_id=player_message_model.user_id,
            rank=player_message_model.rank,
            avatar_id=player_message_model.avatar_id,
        )
        return player
    

class GameOptionsMapper():

    @classmethod
    def map(cls, game_options_message_model: GameOptionsMessageModel) -> GameOptionsModel:
        game_options = GameOptionsModel(
            action_success_mode=game_options_message_model.action_success_mode,
            action_detection_mode=game_options_message_model.action_detection_mode,
            equipment_shop_mode=game_options_message_model.equipment_shop_mode,
            support_actions_mode=game_options_message_model.support_actions_mode,
            initial_asset_stage=game_options_message_model.initial_asset_stage,
            initial_action_mode=game_options_message_model.initial_action_mode,
            manual_def_type_mode=game_options_message_model.manual_def_type_mode,
            infinite_shields=game_options_message_model.infiniteShields,
            multi_target_success=game_options_message_model.multiTargetSuccess,
            defender_actions_detectable=game_options_message_model.defenderActionsDetectable,
            availability_penalty=game_options_message_model.availabilityPenalty,
            defender_pre_setup_mode=game_options_message_model.defenderPreSetupMode,
        )
        return game_options
    
    
class GameOptionLocksMapper():

    @classmethod
    def map(cls, game_option_locks_message_model: GameOptionLocksMessageModel) -> GameOptionLocksModel:
        game_option_locks = GameOptionLocksModel(
            action_success_mode=game_option_locks_message_model.action_success_mode,
            action_detection_mode=game_option_locks_message_model.action_detection_mode,
            equipment_shop_mode=game_option_locks_message_model.equipment_shop_mode,
            support_actions_mode=game_option_locks_message_model.support_actions_mode,
            initial_asset_stage=game_option_locks_message_model.initial_asset_stage,
            initial_action_mode=game_option_locks_message_model.initial_action_mode,
            manual_def_type_mode=game_option_locks_message_model.manual_def_type_mode,
            infinite_shields=game_option_locks_message_model.infiniteShields,
            multi_target_success=game_option_locks_message_model.multiTargetSuccess,
            defender_actions_detectable=game_option_locks_message_model.defenderActionsDetectable,
            availability_penalty=game_option_locks_message_model.availabilityPenalty,
            defender_pre_setup_mode=game_option_locks_message_model.defenderPreSetupMode,
        )
        return game_option_locks
    

class SlotInfoMapper():

    @classmethod
    def map(cls, slot_info_message_model: SlotInfoMessageModel) -> SlotInfoModel:
        slot_info = SlotInfoModel(
            slot_id=slot_info_message_model.slotId,
            name=slot_info_message_model.name,
            type=slot_info_message_model.type,
            is_ready=slot_info_message_model.isReady,
        )
        return slot_info
    

class ScenarioTeaserMapper():

    @classmethod
    def map(cls, scenario_teaser_message_model: ScenarioTeaserMessageModel) -> ScenarioTeaserModel:
        scenario_teaser = ScenarioTeaserModel(
            id=scenario_teaser_message_model.id,
            name=scenario_teaser_message_model.name,
            description=scenario_teaser_message_model.description,
            available_slots=[SlotInfoMapper.map(slot) for slot in scenario_teaser_message_model.availableSlots],
        )
        return scenario_teaser
    

class GoalDescMapper():

    @classmethod
    def map(cls, goal_desc_message_model: GoalDescMessageModel) -> GoalDescModel:
        goal_desc = GoalDescModel(
            id=goal_desc_message_model.id,
            description=goal_desc_message_model.description,
            is_default=goal_desc_message_model.isDefault,
        )
        return goal_desc


class LobbyMapper():

    @classmethod
    def map(cls, lobby_message_model: LobbyMessageModel) -> LobbyModel:
        if lobby_message_model.players is None:
            players = {}
        else:
            players = {
                key: PlayerMapper.map(player) 
                for key, player in lobby_message_model.players.items()
            }
        if lobby_message_model.availableGoals is None:
            available_goals = []
        else:
            available_goals = [
                GoalDescMapper.map(goal_desc)
                for goal_desc in lobby_message_model.availableGoals
            ]
        if lobby_message_model.scenario is None:
            scenario = None
        else:
            scenario = ScenarioTeaserMapper.map(lobby_message_model.scenario)
        lobby = LobbyModel(
            admin=PlayerMapper.map(lobby_message_model.admin),
            code=lobby_message_model.code,
            game_options=GameOptionsMapper.map(lobby_message_model.game_options),
            game_option_locks=GameOptionLocksMapper.map(lobby_message_model.gameOptionLocks),
            players=players,
            scenario=scenario,
            available_goals=available_goals,
            xp_event=lobby_message_model.xpEvent,
            seed=lobby_message_model.seed,
        )
        return lobby


class EffectMapper():

    @classmethod
    def map(cls, effect_message_model: EffectMessageModel) -> EffectModel:
        if effect_message_model.equipment is None:
            equipment = []
        else:
            equipment = [
                EquipmentTemplateMapper.map(eq) 
                for eq in effect_message_model.equipment
            ]
        effect = EffectModel(
            id=effect_message_model.id,
            type=effect_message_model.type,
            name=effect_message_model.name,
            description=effect_message_model.description,
            is_permanent=effect_message_model.isPermanent,
            owner_id=effect_message_model.owner_id,
            scope=effect_message_model.scope,
            active=effect_message_model.active,
            attributes=effect_message_model.attributes,
            equipment=equipment,
            num_effects=effect_message_model.num_effects,
            probability=effect_message_model.probability,
            turns=effect_message_model.turns,
            value=effect_message_model.value
        )
        return effect


class EquipmentTemplateMapper():

    @classmethod
    def map(cls, equipment_message_model: EquipmentTemplateMessageModel) -> EquipmentTemplateModel:
        if equipment_message_model.effects is None:
            effects = []
        else:
            effects = [
                EffectMapper.map(effect) 
                for effect in equipment_message_model.effects
            ]
        if equipment_message_model.impact is None:
            impact = DamageModel(0, 0, 0)
        else:
            impact = DamageModel(*equipment_message_model.impact)
        equipment_template = EquipmentTemplateModel(
            id=equipment_message_model.id,
            type=equipment_message_model.type,
            name=equipment_message_model.name,
            short_description=equipment_message_model.short_description,
            long_description=equipment_message_model.long_description,
            price=equipment_message_model.price,
            is_passive_equipment=equipment_message_model.isPassiveEquipment,
            possible_asset_categories=equipment_message_model.possibleAssetCategories,
            is_single_use=equipment_message_model.isSingleUse,
            impact=impact,
            effects=effects,
            possible_actions=equipment_message_model.possible_actions,
            possible_asset_ids=equipment_message_model.possibleAssetIds,
        )
        return equipment_template


class EquipmentMapper():

    @classmethod
    def map(cls, equipment_message_model: EquipmentMessageModel) -> EquipmentModel:
        if equipment_message_model.effects is None:
            effects = []
        else:
            effects = [
                EffectMapper.map(effect) 
                for effect in equipment_message_model.effects
            ]
        if equipment_message_model.impact is None:
            impact = DamageModel(0, 0, 0)
        else:
            impact = DamageModel(*equipment_message_model.impact)
        equipment = EquipmentModel(
            id=equipment_message_model.id,
            template_id=equipment_message_model.template_id,
            type=equipment_message_model.type,
            name=equipment_message_model.name,
            short_description=equipment_message_model.short_description,
            long_description=equipment_message_model.long_description,
            price=equipment_message_model.price,
            is_passive_equipment=equipment_message_model.isPassiveEquipment,
            possible_asset_categories=equipment_message_model.possibleAssetCategories,
            is_single_use=equipment_message_model.isSingleUse,
            impact=impact,
            effects=effects,
            possible_actions=equipment_message_model.possible_actions,
            possible_asset_ids=equipment_message_model.possibleAssetIds,
            active=equipment_message_model.active,
            equipt_on_action=equipment_message_model.equipt_on_action,
            equipt_on_asset=equipment_message_model.equipt_on_asset,
            used_on_action=equipment_message_model.used_on_action,
            used_on_asset=equipment_message_model.used_on_asset,
            owner_id=equipment_message_model.owner,
            is_used=equipment_message_model.isUsed,
            is_reusable=equipment_message_model.isReusable,
            is_attack_equipment=equipment_message_model.isAttackEquipment,
            is_defense_equipment=equipment_message_model.isDefenseEquipment,
        )
        return equipment


class ActionEventMapper():

    @classmethod
    def map(cls, action_event_message_model: ActionEventMessageModel) -> ActionEventModel:
        if action_event_message_model.current_asset_damage is None:
            current_asset_damage = DamageModel(0, 0, 0)
        else:
            current_asset_damage = DamageModel(*action_event_message_model.current_asset_damage)
        if action_event_message_model.damage_dealt is None:
            damage_dealt = DamageModel(0, 0, 0)
        else:
            damage_dealt = DamageModel(*action_event_message_model.damage_dealt)
        if action_event_message_model.active_damage is None:
            active_damage = DamageModel(0, 0, 0)
        else:
            active_damage = DamageModel(*action_event_message_model.active_damage)
        action_event = ActionEventModel(
            turn_detected=action_event_message_model.turn_detected,
            succeeded=action_event_message_model.succeeded,
            deflected=action_event_message_model.deflected,
            deflected_by=action_event_message_model.deflectedBy,
            deflected_damage=DamageModel(*action_event_message_model.deflectedDamage),
            asset_id=action_event_message_model.asset,
            current_asset_damage=current_asset_damage,
            applied_dependency_damage=action_event_message_model.applied_dependency_damage,
            damage_dealt=damage_dealt,
            active_damage=active_damage,
            countered=action_event_message_model.countered,
            fully_countered=action_event_message_model.fully_countered,
            counters=action_event_message_model.counters,
            is_counterable=action_event_message_model.isCounterable,
            last_turn_to_counter=action_event_message_model.lastTurnToCounter,
            attack_mask_used=action_event_message_model.attackMaskUsed,
        )
        return action_event


class ActionTemplateMapper():

    @classmethod
    def map(cls, action_template_message_model: ActionTemplateMessageModel) -> ActionTemplateModel:
        if action_template_message_model.affectedAttackActions is None:
            affected_attack_actions = []
        else:
            affected_attack_actions = action_template_message_model.affectedAttackActions
        if action_template_message_model.affectedDefenseActions is None:
            affected_defense_actions = []
        else:
            affected_defense_actions = action_template_message_model.affectedDefenseActions
        action_template = ActionTemplateModel(
            id=action_template_message_model.id,
            name=action_template_message_model.name,
            short_description=action_template_message_model.short_description,
            long_description=action_template_message_model.long_description,
            effects=[EffectMapper.map(effect) for effect in action_template_message_model.effects],
            impact=DamageModel(*action_template_message_model.impact),
            soph_requirement=action_template_message_model.soph_requirement,
            requires_admin=action_template_message_model.requiresAdmin,
            required_equipment=[EquipmentTemplateMapper.map(eq) for eq in action_template_message_model.requiredEquipment],
            asset_categories=action_template_message_model.asset_categories,
            attack_stage=action_template_message_model.attack_stage,
            oses=action_template_message_model.oses,
            card_type=action_template_message_model.card_type,
            actor_type=action_template_message_model.actor_type,
            action_point_cost=action_template_message_model.actionPointCost,
            success_chance=action_template_message_model.success_chance,
            detection_chance=action_template_message_model.detection_chance,
            detection_chance_failed=action_template_message_model.detection_chance_failed,
            target_type=action_template_message_model.target_type,
            predefined_attack_mask=action_template_message_model.predefined_attack_mask,
            requires_attack_mask=action_template_message_model.requires_attack_mask,
            def_type=action_template_message_model.def_type,
            possible_actions=action_template_message_model.possible_actions,
            affected_attack_actions=affected_attack_actions,
            affected_defense_actions=affected_defense_actions,
        )
        return action_template


class ActionMapper():

    @classmethod
    def map(cls, action_message_model: ActionMessageModel) -> ActionModel:
        if action_message_model.affectedAttackActions is None:
            affected_attack_actions = []
        else:
            affected_attack_actions = action_message_model.affectedAttackActions
        if action_message_model.affectedDefenseActions is None:
            affected_defense_actions = []
        else:
            affected_defense_actions = action_message_model.affectedDefenseActions
        if action_message_model.equipment_played_with is None:
            equipment_played_with = []
        else:
            equipment_played_with = [
                EquipmentMapper.map(eq) if isinstance(eq, EquipmentMessageModel) else eq 
                for eq in action_message_model.equipment_played_with
            ]
        if action_message_model.supported_by is None:
            supported_by = []
        else:
            supported_by = [
                ActionMapper.map(sa)
                for sa in action_message_model.supported_by
            ]
        if action_message_model.events is None:
            events = []
        else:
            events = [
                ActionEventMapper.map(event) 
                for event in action_message_model.events
            ]
        if action_message_model.deflectedDamage is None:
            deflected_damage = DamageModel(0, 0, 0)
        else:
            deflected_damage = DamageModel(*action_message_model.deflectedDamage)
        action = ActionModel(
            id=action_message_model.id,
            template_id=action_message_model.template_id,
            name=action_message_model.name,
            short_description=action_message_model.short_description,
            long_description=action_message_model.long_description,
            effects=[EffectMapper.map(effect) for effect in action_message_model.effects],
            impact=DamageModel(*action_message_model.impact),
            soph_requirement=action_message_model.soph_requirement,
            requires_admin=action_message_model.requiresAdmin,
            required_equipment=[EquipmentTemplateMapper.map(eq) for eq in action_message_model.requiredEquipment],
            asset_categories=action_message_model.asset_categories,
            attack_stage=action_message_model.attack_stage,
            oses=action_message_model.oses,
            card_type=action_message_model.card_type,
            actor_type=action_message_model.actor_type,
            action_point_cost=action_message_model.actionPointCost,
            success_chance=action_message_model.success_chance,
            detection_chance=action_message_model.detection_chance,
            detection_chance_failed=action_message_model.detection_chance_failed,
            target_type=action_message_model.target_type,
            predefined_attack_mask=action_message_model.predefined_attack_mask,
            requires_attack_mask=action_message_model.requires_attack_mask,
            def_type=action_message_model.def_type,
            possible_actions=action_message_model.possible_actions,
            affected_attack_actions=affected_attack_actions,
            affected_defense_actions=affected_defense_actions,
            actor_id=action_message_model.actor,
            attack_mask_used=action_message_model.attack_mask_used,
            equipment_played_with=equipment_played_with,
            events=events,
            supported_by=supported_by,
            deflected_damage=deflected_damage,
            is_used=action_message_model.isUsed,
        )
        return action


class AssetMapper():

    @classmethod
    def map(cls, asset_message_model: AssetMessageModel) -> AssetModel:
        if asset_message_model.permanent_effects is None:
            permanent_effects = []
        else:
            permanent_effects = [
                EffectMapper.map(effect) 
                for effect in asset_message_model.permanent_effects
            ]
        if asset_message_model.played_actions is None:
            played_actions = []
        else:
            played_actions = [
                ActionMapper.map(action_event)
                for action_event in asset_message_model.played_actions
            ]
        if asset_message_model.exposed is None:
            exposed = ExposedModel(0, 0, 0)
        else:
            exposed = ExposedModel(*asset_message_model.exposed)
        if asset_message_model.damage is None:
            damage = DamageModel(0, 0, 0)
        else:
            damage = DamageModel(*asset_message_model.damage)
        asset = AssetModel(
            id=asset_message_model.id,
            name=asset_message_model.name,
            category=asset_message_model.category,
            attack_stage=asset_message_model.attack_stage,
            active_exploits=[EquipmentMapper.map(eq) for eq in asset_message_model.active_exploits],
            has_admin_rights=asset_message_model.hasAdminRights,
            is_offline=asset_message_model.isOffline,
            description=asset_message_model.description,
            initially_exposed=asset_message_model.initially_exposed,
            os=asset_message_model.os,
            parent_asset=asset_message_model.parent_asset,
            child_assets=asset_message_model.child_assets,
            exposed=exposed,
            damage=damage,
            attack_vectors=asset_message_model.attack_vectors,
            dependencies=asset_message_model.dependencies,
            permanent_effects=permanent_effects,
            played_actions=played_actions,
            shield=asset_message_model.shield,
            has_been_seen=asset_message_model.hasBeenSeen,
        )
        return asset


class GoalMapper():

    @classmethod
    def map(cls, goal_message_model: GoalMessageModel) -> GoalModel:
        if not hasattr(goal_message_model, 'asset') or goal_message_model.asset is None:
            asset = None
        else:
            asset = AssetMapper.map(goal_message_model.asset)
        goal = GoalModel(
            type=goal_message_model.type,
            asset=asset,
            damage=DamageModel(*goal_message_model.damage),
            attack_stage=goal_message_model.attack_stage,
            credits=goal_message_model.credits,
            defender=goal_message_model.defender,
            exposed=goal_message_model.exposed,
            ins=goal_message_model.ins,
        )
        return goal


class ActorMapper():

    @classmethod
    def map(cls, actor_message_model: ActorMessageModel) -> ActorModel:
        if actor_message_model.visible_assets is None:
            visible_assets = []
        else:
            visible_assets = [
                AssetMapper.map(asset)
                for asset in actor_message_model.visible_assets
            ]
        if actor_message_model.actions is None:
            actions = []
        else:
            actions = [
                ActionMapper.map(action)
                for action in actor_message_model.actions
            ]
        if actor_message_model.goals is None:
            goals = [[]]
        else:
            goals = [
                [GoalMapper.map(goal) for goal in goalgroup]
                for goalgroup in actor_message_model.goals
            ]
        if actor_message_model.assets is None:
            assets = []
        else:
            assets = [
                AssetMapper.map(asset)
                for asset in actor_message_model.assets
            ]
        if actor_message_model.equipment is None:
            equipment = []
        else:
            equipment = [
                EquipmentMapper.map(equipment)
                for equipment in actor_message_model.equipment
            ]
        actor = ActorModel(
            id=actor_message_model.id,
            connection_id=actor_message_model.connection_id,
            user_id=actor_message_model.user_id,
            avatar_id=actor_message_model.avatar_id,
            online=actor_message_model.online,
            name=actor_message_model.name,
            description=actor_message_model.description,
            soph=actor_message_model.soph,
            det=actor_message_model.det,
            wealth=actor_message_model.wealth,
            ins=actor_message_model.ins,
            ini=actor_message_model.ini,
            credits=actor_message_model.credits,
            insight_shield=actor_message_model.insight_shield,
            actions=actions,
            equipment=equipment,
            visible_assets=visible_assets,
            goal_description=actor_message_model.goal_description,
            mission_description=actor_message_model.mission_description,
            goals=goals,
            assets=assets,
            has_been_detected=actor_message_model.has_been_detected,
            type=actor_message_model.type,
            action_points=actor_message_model.action_points,
        )
        return actor
  

class GameMapper():

    @classmethod
    def map(cls, game_message_model: GameMessageModel) -> GameModel:
        game = GameModel(
            actions_offered=[ActionTemplateMapper.map(at) for at in game_message_model.actions_offered],
            amount_selection=game_message_model.amount_selection,
            phase=game_message_model.phase,
            players=[PlayerMapper.map(player) for player in game_message_model.players],
            roles={key: ActorMapper.map(role) for key, role in game_message_model.roles.items()},
            scenario_description=game_message_model.scenarioDescription,
            scenario_name=game_message_model.scenarioName,
            scenario_id=game_message_model.scenario_id,
            shop=[EquipmentTemplateMapper.map(eq) for eq in game_message_model.shop],
            turn=game_message_model.turn,
        )
        return game
    

class ErrorsMapper():

    @classmethod
    def map(cls, errors_message_model: ErrorsMessageModel) -> ErrorsModel:
        errors = ErrorsModel(
            error_id=errors_message_model.error_id,
            error_message=errors_message_model.error_message,
            multiple_errors=errors_message_model.multiple_errors,
        )
        return errors
    

class ActionChanceModifierMapper():

    @classmethod
    def map(cls, acm_message_model: ActionChanceModifierMessageModel) -> ActionChanceModifierModel:
        acm = ActionChanceModifierModel(
            bonus=acm_message_model.bonus,
            reason=acm_message_model.reason,
        )
        return acm
    

class AssetChangesMapper():

    @classmethod
    def map(cls, acm_message_model: AssetChangesMessageModel) -> AssetChangesModel:
        acm = AssetChangesModel(
            hidden=acm_message_model.hidden,
            revealed=[AssetMapper.map(asset) for asset in acm_message_model.revealed],
        )
        return acm
    

class PostGameSummaryMapper():

    @classmethod
    def map(cls, post_game_summary_message_model: PostGameSummaryMessageModel) -> PostGameSummaryModel:
        post_game_summary = PostGameSummaryModel(
            end_state=post_game_summary_message_model.endState,
            turns_played=post_game_summary_message_model.turnsPlayed,
            attacker_undetected_turns=post_game_summary_message_model.attackerUndetectedTurns,
            actions_detected=post_game_summary_message_model.actionsDetected,
            damage_dealt=post_game_summary_message_model.damageDealt,
            damage_healed=post_game_summary_message_model.damageHealed,
            equipment_purchased=post_game_summary_message_model.equipmentPurchased,
            credits_spent=post_game_summary_message_model.creditsSpent,
            actions_succeeded=post_game_summary_message_model.actionsSucceeded,
            credits_spent_total=post_game_summary_message_model.creditsSpentTotal,
        )
        return post_game_summary

class EventEntryMapper():

    @classmethod
    def map(cls, event_entry_message_model: EventEntryMessageModel) -> EventEntryModel:
        event_entry = EventEntryModel(
            id=event_entry_message_model.id,
            created=event_entry_message_model.created,
            type=event_entry_message_model.type,
        )
        return event_entry


class SelectedActionMapper():

    @classmethod
    def map(cls, selected_action_message_model: SelectedActionMessageModel) -> SelectedActionModel:
        selected_action = SelectedActionModel(
            id=selected_action_message_model.id,
            amount=selected_action_message_model.amount,
        )
        return selected_action