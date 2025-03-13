import unittest

from penquest_pkgs.constants import (
    ActorType,
    MIN_ACTION_POINTS,
    AssetCategory,
    OS,
    AttackStage,
)
from penquest_pkgs.game.actor_helper import ActorHelper

class TestActorHelper(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_get_min_aps_defender(self):
        defender = type("ActorModel", (object, ), {"type": ActorType.DEFENCE})()
        self.assertEqual(defender.type, ActorType.DEFENCE)

        min_aps = ActorHelper.get_min_aps(defender)
        self.assertEqual(min_aps, MIN_ACTION_POINTS)

    def test_get_min_aps_attacker_not_last_turn(self):
        attacker = type("ActorModel", (object, ), {"type": ActorType.ATTACK, "ini": 1})()
        self.assertEqual(attacker.type, ActorType.ATTACK)
        self.assertGreater(attacker.ini, 0)

        min_aps = ActorHelper.get_min_aps(attacker)
        self.assertEqual(min_aps, MIN_ACTION_POINTS)

    def test_get_min_aps_attacker_last_turn(self):
        attacker = type("ActorModel", (object, ), {"type": ActorType.ATTACK, "ini": 0})()
        self.assertEqual(attacker.type, ActorType.ATTACK)
        self.assertEqual(attacker.ini, 0)

        min_aps = ActorHelper.get_min_aps(attacker)
        self.assertEqual(min_aps, 0)

    def test_get_visible_asset_properties(self):
        offline_asset = type(
            "Asset",
            (object, ),
            {
                "is_offline": True, 
                "category": AssetCategory.APP_SERVER,
                "os": OS.LINUX,
                "attack_stage": AttackStage.RECONNAISSENCE,
                "has_admin_rights": False,
            }
        )()
        online_asset_1 = type(
            "Asset",
            (object, ),
            {
                "is_offline": False, 
                "category": AssetCategory.WEB_SERVER,
                "os": OS.WINDOWS,
                "attack_stage": AttackStage.EXECUTION,
                "has_admin_rights": True,
            }
        )()
        online_asset_2 = type(
            "Asset",
            (object, ),
            {
                "is_offline": False, 
                "category": AssetCategory.CLIENT,
                "os": OS.LINUX,
                "attack_stage": AttackStage.INITIAL_ACCESS,
                "has_admin_rights": False,
            }
        )()
        online_asset_3 = type(
            "Asset",
            (object, ),
            {
                "is_offline": False, 
                "category": AssetCategory.MOBILE,
                "os": OS.ANDROID,
                "attack_stage": AttackStage.RECONNAISSENCE,
                "has_admin_rights": False,
            }
        )()
        assets = [
            offline_asset,
            online_asset_1,
            online_asset_2,
            online_asset_3,
        ]

        self.assertTrue(offline_asset.is_offline)
        self.assertFalse(online_asset_1.is_offline)
        self.assertFalse(online_asset_2.is_offline)
        self.assertFalse(online_asset_3.is_offline)

        asset_properties = ActorHelper.get_visible_asset_properties(assets)
        self.assertEqual(len(asset_properties), 6)
        self.assertIn(
            (AssetCategory.WEB_SERVER, OS.WINDOWS, AttackStage.RECONNAISSENCE, True),
            asset_properties
        )
        self.assertIn(
            (AssetCategory.WEB_SERVER, OS.WINDOWS, AttackStage.INITIAL_ACCESS, True),
            asset_properties
        )
        self.assertIn(
            (AssetCategory.WEB_SERVER, OS.WINDOWS, AttackStage.EXECUTION, True),
            asset_properties
        )
        self.assertIn(
            (AssetCategory.CLIENT, OS.LINUX, AttackStage.RECONNAISSENCE, False),
            asset_properties
        )
        self.assertIn(
            (AssetCategory.CLIENT, OS.LINUX, AttackStage.INITIAL_ACCESS, False),
            asset_properties
        )
        self.assertIn(
            (AssetCategory.MOBILE, OS.ANDROID, AttackStage.RECONNAISSENCE, False),
            asset_properties
        )
        