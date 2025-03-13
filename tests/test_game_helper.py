import unittest
from unittest.mock import patch

from penquest_pkgs.constants import (
    CardType,
    EquipmentType,
    PERMANENT_EQUIPMENT_TYPES,
    TargetType,
    DefType,
    CIA,
)
from penquest_pkgs.model import (
    DamageModel,
    GameStateModel,
    ActorModel,
    ValidatedPlayActionModel,
)
from penquest_pkgs.game.game_helper import GameHelper
from penquest_pkgs.game.action_validation_helper import ActionValidationHelper
from penquest_pkgs.game.actor_helper import ActorHelper
from penquest_pkgs.game.action_helper import ActionHelper
from penquest_pkgs.exceptions import PenQuestException, Errors

GAME_HELPER = "penquest_pkgs.game.game_helper.GameHelper"
ACTION_VALIDATION_HELPER = "penquest_pkgs.game.action_validation_helper.ActionValidationHelper"
ACTOR_HELPER = "penquest_pkgs.game.actor_helper.ActorHelper"
ACTION_HELPER = "penquest_pkgs.game.action_helper.ActionHelper"

class TestGameHelper(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_get_all_action_combs(self):
        main_action_1 = type(
            "ActionModel",
            (object, ),
            {"card_type": CardType.MAIN},
        )()
        main_action_2 = type(
            "ActionModel",
            (object, ),
            {"card_type": CardType.MAIN},
        )()
        support_action_1 = type(
            "ActionModel",
            (object, ),
            {"card_type": CardType.SUPPORT},
        )()
        support_action_2 = type(
            "ActionModel",
            (object, ),
            {"card_type": CardType.SUPPORT},
        )()
        equipment_1 = type(
            "EquipmentModel",
            (object,),
            {"type": EquipmentType.MALWARE}
        )()
        equipment_2 = type(
            "EquipmentModel",
            (object,),
            {"type": EquipmentType.EXPLOIT}
        )()
        actor = type(
            "ActorModel",
            (object,),
            {
                "hand": [
                    main_action_1,
                    main_action_2,
                    support_action_1,
                    support_action_2,
                ],
                "equipment": [equipment_1, equipment_2]
            }
        )()
        self.assertEqual(main_action_1.card_type, CardType.MAIN)
        self.assertEqual(main_action_2.card_type, CardType.MAIN)
        self.assertEqual(support_action_1.card_type, CardType.SUPPORT)
        self.assertEqual(support_action_2.card_type, CardType.SUPPORT)
        self.assertNotIn(equipment_1.type, PERMANENT_EQUIPMENT_TYPES)
        self.assertNotIn(equipment_2.type, PERMANENT_EQUIPMENT_TYPES)
        
        self.assertIn(main_action_1, actor.hand)
        self.assertIn(main_action_2, actor.hand)
        self.assertIn(support_action_1, actor.hand)
        self.assertIn(support_action_1, actor.hand)
        self.assertIn(equipment_1, actor.equipment)
        self.assertIn(equipment_2, actor.equipment)

        action_combs = GameHelper.get_all_action_combs(actor)
        self.assertEqual(len(action_combs), 18)
        self.assertIn((main_action_1, None, None), action_combs)
        self.assertIn((main_action_1, None, equipment_1), action_combs)
        self.assertIn((main_action_1, None, equipment_2), action_combs)
        self.assertIn((main_action_1, support_action_1, None), action_combs)
        self.assertIn((main_action_1, support_action_1, equipment_1), action_combs)
        self.assertIn((main_action_1, support_action_1, equipment_2), action_combs)
        self.assertIn((main_action_1, support_action_2, None), action_combs)
        self.assertIn((main_action_1, support_action_2, equipment_1), action_combs)
        self.assertIn((main_action_1, support_action_2, equipment_2), action_combs)
        self.assertIn((main_action_2, None, None), action_combs)
        self.assertIn((main_action_2, None, equipment_1), action_combs)
        self.assertIn((main_action_2, None, equipment_2), action_combs)
        self.assertIn((main_action_2, support_action_1, None), action_combs)
        self.assertIn((main_action_2, support_action_1, equipment_1), action_combs)
        self.assertIn((main_action_2, support_action_1, equipment_2), action_combs)
        self.assertIn((main_action_2, support_action_2, None), action_combs)
        self.assertIn((main_action_2, support_action_2, equipment_1), action_combs)
        self.assertIn((main_action_2, support_action_2, equipment_2), action_combs)

    def test_get_possible_response_targets_no_heal(self):
        game_state = type("GameStateModel", (object, ), {})()
        main_action = type(
            "ActionModel",
            (object, ),
            {
                "id": 1,
                "has_heal_part": False,
            },
        )()
        asset = type(
            "AssetModel",
            (object,),
            { "id": 1 },
        )()
        attack_mask = "C"
        self.assertFalse(main_action.has_heal_part)

        possible_response_targets = GameHelper.get_possible_response_targets(
            game_state,
            main_action,
            asset,
            attack_mask
        )
        self.assertEqual(len(possible_response_targets), 0)
        self.assertEqual(possible_response_targets, [])

    def test_get_possible_response_targets(self):
        def true_func(*args):
            return True
        def false_func(*args):
            return False
        game_state = type("GameStateModel", (object, ), {})()
        main_action = type(
            "ActionModel",
            (object, ),
            {
                "id": 1,
                "has_heal_part": True,
                "affected_attack_actions": [1],
                "affected_defense_actions": [2],
                "impact": DamageModel(-1, -1, -1),
            },
        )()
        no_heal_action = type(
            "ActionModel",
            (object, ),
            {
                "id": 1,
                "has_heal_part": True,
                "affected_attack_actions": [1],
                "affected_defense_actions": [2],
                "impact": DamageModel(0, 0, 0),
            },
        )()
        invalid_action = type(
            "ActionModel",
            (object, ),
            {"id": 2, "template_id": 3}
        )()
        valid_action_1 = type(
            "ActionModel",
            (object, ),
            {"id": 3, "template_id": 1}
        )()
        valid_action_2 = type(
            "ActionModel",
            (object, ),
            {"id": 4, "template_id": 2}
        )()
        no_asset_event = type(
            "ActionEventModel",
            (object, ),
            {
                "asset_id": None,
                "attack_mask_used": "CIA",
                "action": invalid_action
            }
        )()
        fully_countered_event = type(
            "ActionEventModel",
            (object, ),
            {
                "asset_id": 1,
                "fully_countered": True,
                "attack_mask_used": "CIA",
                "action": invalid_action
            }
        )()
        no_active_damage_event = type(
            "ActionEventModel",
            (object, ),
            {
                "asset_id": 1, 
                "fully_countered": False, 
                "active_damage": DamageModel(0, 0, 0),
                "attack_mask_used": "CIA",
                "action": invalid_action
            }
        )()
        no_affected_action_event = type(
            "ActionEventModel",
            (object, ),
            {
                "asset_id": 1, 
                "fully_countered": False, 
                "active_damage": DamageModel(1, 0, 1),
                "attack_mask_used": "CIA",
                "action": invalid_action
            }
        )()
        no_overlapping_mask_event = type(
            "ActionEventModel",
            (object, ),
            {
                "asset_id": 1, 
                "fully_countered": False, 
                "active_damage": DamageModel(1, 0, 1),
                "attack_mask_used": "A",
                "action": valid_action_1
            }
        )()
        not_counterable_event = type(
            "ActionEventModel",
            (object, ),
            {
                "asset_id": 1, 
                "fully_countered": False, 
                "active_damage": DamageModel(1, 0, 1),
                "attack_mask_used": "A",
                "action": valid_action_1,
                "is_currently_counterable": false_func,
            }
        )()
        event_1 = type(
            "ActionEventModel",
            (object, ),
            {
                "asset_id": 1, 
                "fully_countered": False, 
                "active_damage": DamageModel(1, 0, 1),
                "attack_mask_used": "CIA",
                "action": valid_action_1,
                "is_currently_counterable": true_func,
            }
        )()
        event_2 = type(
            "ActionEventModel",
            (object, ),
            {
                "asset_id": 1, 
                "fully_countered": False, 
                "active_damage": DamageModel(0, 2, 1),
                "attack_mask_used": "CIA",
                "action": valid_action_2,
                "is_currently_counterable": true_func,
            }
        )()
        asset = type(
            "AssetModel",
            (object,),
            {
                "id": 1,
                "played_actions": [
                    no_asset_event,
                    fully_countered_event,
                    no_active_damage_event,
                    no_affected_action_event,
                    no_overlapping_mask_event,
                    not_counterable_event,
                    event_1,
                    event_2
                ]
            }
        )()
        attack_mask = "C"
        # setup checks for negatives
        self.assertIsNone(no_asset_event.asset_id)
        self.assertTrue(fully_countered_event.fully_countered)
        self.assertFalse(any([c > 0 for c in no_active_damage_event.active_damage]))
        self.assertNotIn(no_affected_action_event.action.template_id, main_action.affected_attack_actions)
        self.assertNotIn(no_affected_action_event.action.template_id, main_action.affected_defense_actions)
        self.assertNotIn(attack_mask, no_overlapping_mask_event.attack_mask_used)
        self.assertFalse(not_counterable_event.is_currently_counterable())
        self.assertFalse(any([c < 0 for c in no_heal_action.impact.apply_mask(attack_mask)]))

        # setup checks for positive event_1
        self.assertIsNotNone(event_1.asset_id)
        self.assertFalse(event_1.fully_countered)
        self.assertTrue(any([c > 0 for c in event_1.active_damage]))
        self.assertIn(event_1.action.template_id, main_action.affected_attack_actions)
        self.assertIn(attack_mask, event_1.attack_mask_used)
        self.assertTrue(event_1.is_currently_counterable())
        self.assertTrue(any([c < 0 for c in main_action.impact.apply_mask(attack_mask)]))

        # setup checks for positive event_2
        self.assertIsNotNone(event_2.asset_id)
        self.assertFalse(event_2.fully_countered)
        self.assertTrue(any([c > 0 for c in event_2.active_damage]))
        self.assertIn(event_2.action.template_id, main_action.affected_defense_actions)
        self.assertIn(attack_mask, event_2.attack_mask_used)
        self.assertTrue(event_2.is_currently_counterable())
        self.assertTrue(any([c < 0 for c in main_action.impact.apply_mask(attack_mask)]))

        no_targets = GameHelper.get_possible_response_targets(
            game_state,
            no_heal_action,
            asset,
            attack_mask
        )
        self.assertEqual(len(no_targets), 0)
        self.assertEqual(no_targets, [])

        possible_response_targets = GameHelper.get_possible_response_targets(
            game_state,
            main_action,
            asset,
            attack_mask
        )
        self.assertEqual(len(possible_response_targets), 2)
        self.assertEqual(possible_response_targets[0].id, 3)
        self.assertEqual(possible_response_targets[1].id, 4)

    def test_get_valid_play_action_combs_support_as_main(self):
        game_state = type("GameStateModel", (object, ), {"role": None, "assets_on_board": None})()
        main_action = type(
            "ActionModel",
            (object, ),
            {"card_type": CardType.SUPPORT}
        )()
        def no_op(*args):
            pass
        def visible_assets(*args):
            return set()
        self.assertEqual(main_action.card_type, CardType.SUPPORT)

        with patch(f"{ACTION_VALIDATION_HELPER}.validate", no_op), \
            patch(f"{ACTOR_HELPER}.get_visible_asset_properties", visible_assets):
            playable_list = GameHelper.get_valid_play_action_combs(
                game_state,
                [(main_action, None, None)]
            )
        self.assertEqual(len(playable_list), 0)
        self.assertEqual(playable_list, [])

    def test_get_valid_play_action_combs_not_playable(self):
        game_state = type("GameStateModel", (object, ), {"role": None, "assets_on_board": None})()
        main_action = type(
            "ActionModel",
            (object, ),
            {"card_type": CardType.MAIN}
        )()
        def add_error(
                game_state: GameStateModel,
                actor: ActorModel,
                validated_action: ValidatedPlayActionModel,
                **kwargs
            ):
            validated_action.errors.append(
                PenQuestException(Errors.ActionActorMismatchError, "some error")
            )
        def visible_assets(*args):
            return set()
        ActionValidationHelper.validate = add_error
        ActorHelper.get_visible_asset_properties = visible_assets
        self.assertEqual(main_action.card_type, CardType.MAIN)

        with patch(f"{ACTION_VALIDATION_HELPER}.validate", add_error), \
            patch(f"{ACTOR_HELPER}.get_visible_asset_properties", visible_assets):
            playable_list = GameHelper.get_valid_play_action_combs(
                game_state,
                [(main_action, None, None)]
            )
        self.assertEqual(len(playable_list), 1)
        self.assertFalse(playable_list[0].is_playable())

    def test_get_valid_play_action_combs_multi_target_attacker(self):
        def false_func(*args):
            return False
        asset_1 = type(
            "AssetModel",
            (object, ),
            {"id": 1, "is_offline": False}
        )()
        asset_2 = type(
            "AssetModel",
            (object, ),
            {"id": 2, "is_offline": True}
        )()
        actor = type(
            "ActorModel",
            (object,),
            {"visible_assets": [asset_1, asset_2], "is_attacker": True}
        )()
        game_state = type("GameStateModel", (object, ), {"role": actor, "assets_on_board": None})()
        main_action = type(
            "ActionModel",
            (object, ),
            {
                "card_type": CardType.MAIN, 
                "target_type": TargetType.MULTI,
                "is_defense_action": false_func,
            }
        )()
        def no_op(*args, **kwargs):
            pass
        def visible_assets(*args):
            return set()
        self.assertEqual(main_action.card_type, CardType.MAIN)
        self.assertNotEqual(main_action.target_type, TargetType.SINGLE)
        self.assertTrue(actor.is_attacker)

        with patch(f"{ACTION_VALIDATION_HELPER}.validate", no_op), \
            patch(f"{ACTOR_HELPER}.get_visible_asset_properties", visible_assets):
            playable_list = GameHelper.get_valid_play_action_combs(
                game_state,
                [(main_action, None, None)]
            )
        self.assertEqual(len(playable_list), 1)
        self.assertTrue(playable_list[0].is_playable())
        self.assertEqual(len(playable_list[0].possible_targets), 1)
        self.assertIn(asset_1, playable_list[0].possible_targets)

    def test_get_valid_play_action_combs_multi_target_defender(self):
        def false_func(*args):
            return False
        asset_1 = type(
            "AssetModel",
            (object, ),
            {"id": 1, "is_offline": False}
        )()
        asset_2 = type(
            "AssetModel",
            (object, ),
            {"id": 2, "is_offline": True}
        )()
        actor = type(
            "ActorModel",
            (object,),
            {"visible_assets": [asset_1, asset_2], "is_attacker": False}
        )()
        game_state = type("GameStateModel", (object, ), {"role": actor, "assets_on_board": None})()
        main_action = type(
            "ActionModel",
            (object, ),
            {
                "card_type": CardType.MAIN, 
                "target_type": TargetType.MULTI,
                "is_defense_action": false_func,
            }
        )()
        def no_op(*args, **kwargs):
            pass
        def visible_assets(*args):
            return set()
        self.assertEqual(main_action.card_type, CardType.MAIN)
        self.assertNotEqual(main_action.target_type, TargetType.SINGLE)
        self.assertFalse(actor.is_attacker)

        with patch(f"{ACTION_VALIDATION_HELPER}.validate", no_op), \
            patch(f"{ACTOR_HELPER}.get_visible_asset_properties", visible_assets):
            playable_list = GameHelper.get_valid_play_action_combs(
                game_state,
                [(main_action, None, None)]
            )
        self.assertEqual(len(playable_list), 1)
        self.assertTrue(playable_list[0].is_playable())
        self.assertEqual(len(playable_list[0].possible_targets), 2)
        self.assertIn(asset_1, playable_list[0].possible_targets)
        self.assertIn(asset_2, playable_list[0].possible_targets)

    def test_get_valid_play_action_combs_single_no_target(self):
        def false_func(*args):
            return False
        asset_1 = type(
            "AssetModel",
            (object, ),
            {"id": 1, "is_offline": False}
        )()
        asset_2 = type(
            "AssetModel",
            (object, ),
            {"id": 2, "is_offline": True}
        )()
        actor = type(
            "ActorModel",
            (object,),
            {"visible_assets": [asset_1, asset_2]}
        )()
        game_state = type("GameStateModel", (object, ), {"role": actor, "assets_on_board": None})()
        main_action = type(
            "ActionModel",
            (object, ),
            {
                "name": "main action",
                "card_type": CardType.MAIN, 
                "target_type": TargetType.SINGLE,
                "is_defense_action": false_func,
            }
        )()
        def no_op(*args, **kwargs):
            pass
        def visible_assets(*args):
            return set()
        def no_targets(*args):
            return []
        self.assertEqual(main_action.card_type, CardType.MAIN)
        self.assertEqual(main_action.target_type, TargetType.SINGLE)

        with patch(f"{ACTION_VALIDATION_HELPER}.validate", no_op), \
            patch(f"{ACTOR_HELPER}.get_visible_asset_properties", visible_assets), \
            patch(f"{ACTION_HELPER}.get_possible_targets", no_targets):
            playable_list = GameHelper.get_valid_play_action_combs(
                game_state,
                [(main_action, None, None)]
            )
        self.assertEqual(len(playable_list), 1)
        self.assertFalse(playable_list[0].is_playable())
        self.assertEqual(len(playable_list[0].possible_targets), 0)

    def test_get_valid_play_action_combs_single_no_target_support(self):
        def false_func(*args):
            return False
        asset_1 = type(
            "AssetModel",
            (object, ),
            {"id": 1, "is_offline": False}
        )()
        asset_2 = type(
            "AssetModel",
            (object, ),
            {"id": 2, "is_offline": True}
        )()
        actor = type(
            "ActorModel",
            (object,),
            {"visible_assets": [asset_1, asset_2]}
        )()
        game_state = type("GameStateModel", (object, ), {"role": actor, "assets_on_board": None})()
        main_action = type(
            "ActionModel",
            (object, ),
            {
                "name": "main action",
                "card_type": CardType.MAIN, 
                "target_type": TargetType.SINGLE,
                "is_defense_action": false_func,
            }
        )()
        support_action = type(
            "ActionModel",
            (object, ),
            {
                "name": "support action",
                "card_type": CardType.SUPPORT, 
                "target_type": TargetType.SINGLE,
                "is_defense_action": false_func,
            }
        )()
        def no_op(*args, **kwargs):
            pass
        def visible_assets(*args):
            return set()
        def no_targets(action, *args):
            if action.card_type == CardType.MAIN:
                return set([asset_1])
            elif action.card_type == CardType.SUPPORT:
                return set([asset_2])
        self.assertEqual(main_action.card_type, CardType.MAIN)
        self.assertEqual(main_action.target_type, TargetType.SINGLE)
        self.assertEqual(support_action.card_type, CardType.SUPPORT)

        with patch(f"{ACTION_VALIDATION_HELPER}.validate", no_op), \
            patch(f"{ACTOR_HELPER}.get_visible_asset_properties", visible_assets), \
            patch(f"{ACTION_HELPER}.get_possible_targets", no_targets):
            playable_list = GameHelper.get_valid_play_action_combs(
                game_state,
                [(main_action, support_action, None)]
            )
        self.assertEqual(len(playable_list), 1)
        self.assertFalse(playable_list[0].is_playable())
        self.assertEqual(len(playable_list[0].possible_targets), 0)

    def test_get_valid_play_action_combs_single_success(self):
        def false_func(*args):
            return False
        asset_1 = type(
            "AssetModel",
            (object, ),
            {"id": 1, "is_offline": False}
        )()
        asset_2 = type(
            "AssetModel",
            (object, ),
            {"id": 2, "is_offline": True}
        )()
        actor = type(
            "ActorModel",
            (object,),
            {"visible_assets": [asset_1, asset_2]}
        )()
        game_state = type("GameStateModel", (object, ), {"role": actor, "assets_on_board": None})()
        main_action = type(
            "ActionModel",
            (object, ),
            {
                "name": "main action",
                "card_type": CardType.MAIN, 
                "target_type": TargetType.SINGLE,
                "is_defense_action": false_func,
            }
        )()
        support_action = type(
            "ActionModel",
            (object, ),
            {
                "name": "support action",
                "card_type": CardType.SUPPORT, 
                "target_type": TargetType.SINGLE,
                "is_defense_action": false_func,
            }
        )()
        def no_op(*args, **kwargs):
            pass
        def visible_assets(*args):
            return set()
        def no_targets(action, *args):
            if action.card_type == CardType.MAIN:
                return set([asset_1])
            elif action.card_type == CardType.SUPPORT:
                return set([asset_1, asset_2])
        self.assertEqual(main_action.card_type, CardType.MAIN)
        self.assertEqual(main_action.target_type, TargetType.SINGLE)
        self.assertEqual(support_action.card_type, CardType.SUPPORT)

        with patch(f"{ACTION_VALIDATION_HELPER}.validate", no_op), \
            patch(f"{ACTOR_HELPER}.get_visible_asset_properties", visible_assets), \
            patch(f"{ACTION_HELPER}.get_possible_targets", no_targets):
            playable_list = GameHelper.get_valid_play_action_combs(
                game_state,
                [(main_action, support_action, None)]
            )
        self.assertEqual(len(playable_list), 1)
        self.assertTrue(playable_list[0].is_playable())
        self.assertEqual(len(playable_list[0].possible_targets), 1)
        self.assertIn(asset_1, playable_list[0].possible_targets)

    def test_get_valid_play_action_combs_no_response(self):
        def true_func(*args):
            return True
        asset_1 = type(
            "AssetModel",
            (object, ),
            {"id": 1, "is_offline": False}
        )()
        asset_2 = type(
            "AssetModel",
            (object, ),
            {"id": 2, "is_offline": True}
        )()
        actor = type(
            "ActorModel",
            (object,),
            {"visible_assets": [asset_1, asset_2]}
        )()
        game_state = type("GameStateModel", (object, ), {"role": actor, "assets_on_board": None})()
        main_action = type(
            "ActionModel",
            (object, ),
            {
                "name": "main action",
                "card_type": CardType.MAIN, 
                "target_type": TargetType.SINGLE,
                "is_defense_action": true_func,
                "def_type": DefType.DETECTION,
            }
        )()
        support_action = type(
            "ActionModel",
            (object, ),
            {
                "name": "support action",
                "card_type": CardType.SUPPORT, 
                "target_type": TargetType.SINGLE,
                "is_defense_action": true_func,
            }
        )()
        def no_op(*args, **kwargs):
            pass
        def visible_assets(*args):
            return set()
        def no_targets(action, *args):
            if action.card_type == CardType.MAIN:
                return set([asset_1])
            elif action.card_type == CardType.SUPPORT:
                return set([asset_1, asset_2])
        def get_response_target(*args, **kwargs):
            response_target = type(
                "ActionModel",
                (object,),
                {"id": 1}
            )()
            return [response_target]
        ActionValidationHelper.validate = no_op
        ActorHelper.get_visible_asset_properties = visible_assets
        ActionHelper.get_possible_targets = no_targets
        self.assertEqual(main_action.card_type, CardType.MAIN)
        self.assertEqual(main_action.target_type, TargetType.SINGLE)
        self.assertEqual(support_action.card_type, CardType.SUPPORT)
        self.assertNotEqual(main_action.def_type, DefType.RESPONSE)

        with patch(f"{ACTION_VALIDATION_HELPER}.validate", no_op), \
            patch(f"{ACTOR_HELPER}.get_visible_asset_properties", visible_assets), \
            patch(f"{ACTION_HELPER}.get_possible_targets", no_targets), \
            patch(f"{GAME_HELPER}.get_possible_response_targets", get_response_target):
            playable_list = GameHelper.get_valid_play_action_combs(
                game_state,
                [(main_action, support_action, None)]
            )
        self.assertEqual(len(playable_list), 1)
        self.assertTrue(playable_list[0].is_playable())
        self.assertEqual(len(playable_list[0].possible_targets), 1)
        self.assertIn(asset_1, playable_list[0].possible_targets)
        self.assertEqual(len(playable_list[0].possible_response_targets), 0)
        self.assertEqual(playable_list[0].possible_response_targets, {})

    def test_get_valid_play_action_combs_response_target_success(self):
        def true_func(*args):
            return True
        asset_1 = type(
            "AssetModel",
            (object, ),
            {"id": 1, "is_offline": False}
        )()
        asset_2 = type(
            "AssetModel",
            (object, ),
            {"id": 2, "is_offline": True}
        )()
        actor = type(
            "ActorModel",
            (object,),
            {"visible_assets": [asset_1, asset_2]}
        )()
        game_state = type("GameStateModel", (object, ), {"role": actor, "assets_on_board": None})()
        main_action = type(
            "ActionModel",
            (object, ),
            {
                "name": "main action",
                "card_type": CardType.MAIN, 
                "target_type": TargetType.SINGLE,
                "is_defense_action": true_func,
                "def_type": DefType.RESPONSE,
                "predefined_attack_mask": "CIA",
            }
        )()
        support_action = type(
            "ActionModel",
            (object, ),
            {
                "name": "support action",
                "card_type": CardType.SUPPORT, 
                "target_type": TargetType.SINGLE,
                "is_defense_action": true_func,
            }
        )()
        response_target = type(
            "ActionModel",
            (object,),
            {"id": 1}
        )()
        def no_op(*args, **kwargs):
            pass
        def visible_assets(*args):
            return set()
        def no_targets(action, *args):
            if action.card_type == CardType.MAIN:
                return set([asset_1])
            elif action.card_type == CardType.SUPPORT:
                return set([asset_1, asset_2])
        def get_response_target(*args, **kwargs):
            return [response_target]
        self.assertEqual(main_action.card_type, CardType.MAIN)
        self.assertEqual(main_action.target_type, TargetType.SINGLE)
        self.assertEqual(support_action.card_type, CardType.SUPPORT)
        self.assertEqual(main_action.def_type, DefType.RESPONSE)

        with patch(f"{ACTION_VALIDATION_HELPER}.validate", no_op), \
            patch(f"{ACTOR_HELPER}.get_visible_asset_properties", visible_assets), \
            patch(f"{ACTION_HELPER}.get_possible_targets", no_targets), \
            patch(f"{GAME_HELPER}.get_possible_response_targets", get_response_target):
            playable_list = GameHelper.get_valid_play_action_combs(
                game_state,
                [(main_action, support_action, None)]
            )
        self.assertEqual(len(playable_list), 1)
        self.assertTrue(playable_list[0].is_playable())
        self.assertEqual(len(playable_list[0].possible_targets), 1)
        self.assertIn(asset_1, playable_list[0].possible_targets)
        self.assertEqual(len(playable_list[0].possible_response_targets), 1)
        self.assertIn(response_target, playable_list[0].possible_response_targets[asset_1.id])

    def test_get_validated_play_actions(self):
        main_action = type(
            "ActionModel",
            (object, ),
            {"id": 1, "card_type": CardType.MAIN}
        )()
        def get_all_action_combs(*args):
            return [(main_action, None, None)]

        def get_valid_play_action_combs(*args):
            return [
                ValidatedPlayActionModel(main_action, [], [])
            ]
        game_state = type("GameStateModel", (object, ), {"assets_on_board": None})()

        with patch(f"{GAME_HELPER}.get_all_action_combs", get_all_action_combs), \
            patch(f"{GAME_HELPER}.get_valid_play_action_combs", get_valid_play_action_combs):
            validated_actions = GameHelper.get_validated_play_actions(game_state)
        self.assertEqual(len(validated_actions), 1)
        self.assertEqual(validated_actions[0].action, main_action)
        self.assertEqual(validated_actions[0].errors, [])

    def test_get_valid_actions(self):
        main_action = type(
            "ActionModel",
            (object, ),
            {"id": 1, "card_type": CardType.MAIN}
        )()
        other_main_action = type(
            "ActionModel",
            (object, ),
            {"id": 2, "card_type": CardType.MAIN}
        )()
        support_action = type(
            "ActionModel",
            (object, ),
            {"id": 24, "card_type": CardType.SUPPORT}
        )()
        equipment = type(
            "EquipmentModel",
            (object,),
            {"id": 1}
        )()
        target_asset = type(
            "AssetModel",
            (object, ),
            {"id": 1}
        )()
        attack_action = type(
            "ActionModel",
            (object, ),
            {"id": 4, "card_type": CardType.MAIN}
        )()
        actor = type(
            "ActorModel",
            (object,),
            {
                #"actions": [main_action, other_main_action, support_action],
                #"equipment": [equipment]
            }
        )()
        game_state = type(
            "GameStateModel",
            (object, ),
            {
                "role": actor,
                "hand": [main_action, other_main_action, support_action],
                "equipment": [equipment]
            }
        )()
        va_not_playable = ValidatedPlayActionModel(
            action=other_main_action,
            support_actions=[],
            equipment=[],
            attack_mask=CIA,
            possible_targets=[target_asset],
            possible_response_targets={target_asset.id: [attack_action]},
            errors=[object()]
        )
        va_main_only = ValidatedPlayActionModel(
            action=main_action,
            support_actions=[],
            equipment=[],
            attack_mask=CIA,
            possible_targets=[target_asset],
            possible_response_targets={target_asset.id: [attack_action]},
            errors=[]
        )
        va_support = ValidatedPlayActionModel(
            action=main_action,
            support_actions=[support_action],
            equipment=[],
            attack_mask=CIA,
            possible_targets=[target_asset],
            possible_response_targets={target_asset.id: [attack_action]},
            errors=[]
        )
        va_equipment = ValidatedPlayActionModel(
            action=main_action,
            support_actions=[],
            equipment=[equipment],
            attack_mask=CIA,
            possible_targets=[target_asset],
            possible_response_targets={target_asset.id: [attack_action]},
            errors=[]
        )
        va_support_equipment = ValidatedPlayActionModel(
            action=main_action,
            support_actions=[support_action],
            equipment=[equipment],
            attack_mask=CIA,
            possible_targets=[target_asset],
            possible_response_targets={target_asset.id: [attack_action]},
            errors=[]
        )
        def get_validated_play_actions(*args):
            return [
                va_not_playable,
                va_main_only,
                va_support,
                va_equipment,
                va_support_equipment
            ]
        
        self.assertFalse(va_not_playable.is_playable())
        self.assertTrue(va_main_only.is_playable())
        self.assertTrue(va_support.is_playable())
        self.assertTrue(va_equipment.is_playable())
        self.assertTrue(va_support_equipment.is_playable())
        
        with patch(f"{GAME_HELPER}.get_validated_play_actions", get_validated_play_actions):
            valid_actions = GameHelper.get_valid_actions(game_state)
        self.assertEqual(len(valid_actions), 4)
        # 1 = index of action on hand
        self.assertNotIn((1,0,0,7,1,4), valid_actions)
        self.assertIn((0,0,0,7,1,4), valid_actions)
        self.assertIn((0,3,0,7,1,4), valid_actions)
        self.assertIn((0,0,1,7,1,4), valid_actions)
        self.assertIn((0,3,1,7,1,4), valid_actions)

    def test_is_any_validated_action_playable_none(self):
        game_state = type(
            "GameStateModel",
            (object, ),
            {"validated_actions": None}
        )()
        self.assertIsNone(game_state.validated_actions)

        outcome = GameHelper.is_any_validated_action_playable(game_state)
        self.assertFalse(outcome)

    def test_is_any_validated_action_playable_zero(self):
        game_state = type(
            "GameStateModel",
            (object, ),
            {"validated_actions": []}
        )()
        self.assertIsNotNone(game_state.validated_actions)
        self.assertEqual(len(game_state.validated_actions), 0)

        outcome = GameHelper.is_any_validated_action_playable(game_state)
        self.assertFalse(outcome)

    def test_is_any_validated_action_playable_true(self):
        def true_func(*args):
            return True
        def false_func(*args):
            return False
        
        game_state = type(
            "GameStateModel",
            (object, ),
            {"validated_actions": [
                type(
                    "ValidatedPlayActionModel",
                    (object, ),
                    {"is_playable": false_func}
                )(),
                type(
                    "ValidatedPlayActionModel",
                    (object, ),
                    {"is_playable": true_func}
                )(),
                type(
                    "ValidatedPlayActionModel",
                    (object, ),
                    {"is_playable": false_func}
                )()
            ]}
        )()
        self.assertIsNotNone(game_state.validated_actions)
        self.assertGreater(len(game_state.validated_actions), 0)
        self.assertTrue(any([x.is_playable() for x in game_state.validated_actions]))

        outcome = GameHelper.is_any_validated_action_playable(game_state)
        self.assertTrue(outcome)

    def test_is_any_validated_action_playable_false(self):
        def false_func(*args):
            return False
        
        game_state = type(
            "GameStateModel",
            (object, ),
            {"validated_actions": [
                type(
                    "ValidatedPlayActionModel",
                    (object, ),
                    {"is_playable": false_func}
                )(),
                type(
                    "ValidatedPlayActionModel",
                    (object, ),
                    {"is_playable": false_func}
                )(),
                type(
                    "ValidatedPlayActionModel",
                    (object, ),
                    {"is_playable": false_func}
                )()
            ]}
        )()
        self.assertIsNotNone(game_state.validated_actions)
        self.assertGreater(len(game_state.validated_actions), 0)
        self.assertFalse(any([x.is_playable() for x in game_state.validated_actions]))

        outcome = GameHelper.is_any_validated_action_playable(game_state)
        self.assertFalse(outcome)

    def test_get_playable_action_combs_none(self):
        game_state = type(
            "GameStateModel",
            (object, ),
            {"validated_actions": None}
        )()
        self.assertIsNone(game_state.validated_actions)

        outcome = GameHelper.get_playable_action_combs(game_state)
        self.assertEqual(len(outcome), 0)

    def test_get_playable_action_combs_zero(self):
        game_state = type(
            "GameStateModel",
            (object, ),
            {"validated_actions": []}
        )()
        self.assertIsNotNone(game_state.validated_actions)
        self.assertEqual(len(game_state.validated_actions), 0)

        outcome = GameHelper.get_playable_action_combs(game_state)
        self.assertEqual(len(outcome), 0)

    def test_get_playable_action_combs_true(self):
        def true_func(*args):
            return True
        def false_func(*args):
            return False
        
        first_action = type(
                "ValidatedPlayActionModel",
                (object, ),
                {"is_playable": false_func}
            )()
        second_action = type(
                "ValidatedPlayActionModel",
                (object, ),
                {"is_playable": true_func}
            )()
        third_action = type(
                "ValidatedPlayActionModel",
                (object, ),
                {"is_playable": false_func}
            )()
        
        game_state = type(
            "GameStateModel",
            (object, ),
            {"validated_actions": [first_action, second_action, third_action ]}
        )()
        self.assertIsNotNone(game_state.validated_actions)
        self.assertGreater(len(game_state.validated_actions), 0)
        self.assertIn(first_action, game_state.validated_actions)
        self.assertIn(second_action, game_state.validated_actions)
        self.assertIn(third_action, game_state.validated_actions)

        outcome = GameHelper.get_playable_action_combs(game_state)
        self.assertEqual(len(outcome), 1)
        self.assertNotIn(first_action, outcome)
        self.assertIn(second_action, outcome)
        self.assertNotIn(third_action, outcome)
