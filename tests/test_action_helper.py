import unittest

from penquest_pkgs.game import ActionHelper
from penquest_pkgs.constants import (
    AssetCategory,
    OS,
    AttackStage,
)

class TestActionHelper(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_get_possible_targets(self):
        correct_tuple_1 = (
            AssetCategory.CLIENT,
            OS.LINUX,
            AttackStage.INITIAL_ACCESS,
            True
        )
        invalid_category_tuple = (
            AssetCategory.DATABASE,
            OS.LINUX,
            AttackStage.INITIAL_ACCESS,
            True
        )
        invalid_os_tuple = (
            AssetCategory.CLIENT,
            OS.ANDROID,
            AttackStage.EXECUTION,
            True
        )
        invalid_attack_stage_tuple = (
            AssetCategory.CLIENT,
            OS.LINUX,
            AttackStage.RECONNAISSENCE,
            True
        )
        missing_admin_tuple = (
            AssetCategory.CLIENT,
            OS.LINUX,
            AttackStage.INITIAL_ACCESS,
            False
        )
        correct_tuple_2 = (
            AssetCategory.CLOUD,
            OS.WINDOWS,
            AttackStage.EXECUTION,
            True
        )
        asset_properties = {
            correct_tuple_1: [type("AssetModel", (object,), {"id": 1})()],
            invalid_category_tuple: [type("AssetModel", (object,), {"id": 2})()],
            invalid_os_tuple: [type("AssetModel", (object,), {"id": 3})()],
            invalid_attack_stage_tuple: [type("AssetModel", (object,), {"id": 4})()],
            missing_admin_tuple: [type("AssetModel", (object,), {"id": 5})()],
            correct_tuple_2: [type("AssetModel", (object,), {"id": 6})()],
        }
        main_action = type(
            "ActionModel",
            (object,),
            {
                "asset_categories": [AssetCategory.CLIENT, AssetCategory.CLOUD],
                "oses": [OS.LINUX, OS.WINDOWS],
                "attack_stage": AttackStage.INITIAL_ACCESS,
                "requires_admin": True,
            }
        )()
        # setup checks for correct_tuple_1
        self.assertIn(correct_tuple_1[0], main_action.asset_categories)
        self.assertIn(correct_tuple_1[1], main_action.oses)
        self.assertGreaterEqual(correct_tuple_1[2], main_action.attack_stage)
        self.assertGreaterEqual(correct_tuple_1[3], main_action.requires_admin)
        # setup checks for correct_tuple_2
        self.assertIn(correct_tuple_2[0], main_action.asset_categories)
        self.assertIn(correct_tuple_2[1], main_action.oses)
        self.assertGreaterEqual(correct_tuple_2[2], main_action.attack_stage)
        self.assertGreaterEqual(correct_tuple_2[3], main_action.requires_admin)
        # setup checks for invalid tuples
        self.assertNotIn(invalid_category_tuple[0], main_action.asset_categories)
        self.assertNotIn(invalid_os_tuple[1], main_action.oses)
        self.assertLess(invalid_attack_stage_tuple[3], main_action.attack_stage)
        self.assertLess(missing_admin_tuple[3], main_action.requires_admin)

        possible_targets = ActionHelper.get_possible_targets(main_action, asset_properties)
        self.assertEqual(len(possible_targets), 2)
        self.assertEqual(possible_targets[0].id, 1)
        self.assertEqual(possible_targets[1].id, 6)
