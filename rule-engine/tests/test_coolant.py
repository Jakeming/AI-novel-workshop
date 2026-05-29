"""
test_coolant.py — TDD for Coolant rule engine.
Vertical slices: one behavior per test.
"""
import sys, os, unittest
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import importlib
Coolant = importlib.import_module("coolant").Coolant
CooldownState = importlib.import_module("coolant").CooldownState
Stage = importlib.import_module("coolant").Stage
UserStatus = importlib.import_module("coolant").UserStatus


def make_status(stage=Stage.novice, cooldown_state=CooldownState.normal,
                cooldown_until=None, failures=0, daily_count=0):
    return UserStatus(
        user_id="test",
        stage=stage,
        can_submit_new_imitation=True,
        cooldown_until=cooldown_until,
        consecutive_failures=failures,
        daily_submit_count=daily_count,
        cooldown_state=cooldown_state,
    )


class TestCheckSubmitAllowed(unittest.TestCase):

    def test_normal_state_allows_submit(self):
        c = Coolant()
        s = make_status()
        self.assertTrue(c.check_submit_allowed(s))

    def test_active_cooldown_blocks_submit(self):
        c = Coolant()
        s = make_status(
            cooldown_state=CooldownState.cooling,
            cooldown_until=datetime.utcnow() + timedelta(hours=1),
        )
        self.assertFalse(c.check_submit_allowed(s))

    def test_expired_cooldown_auto_resets(self):
        c = Coolant()
        s = make_status(
            cooldown_state=CooldownState.cooling,
            cooldown_until=datetime.utcnow() - timedelta(hours=1),
        )
        self.assertTrue(c.check_submit_allowed(s))
        self.assertEqual(s.cooldown_state, CooldownState.normal)
        self.assertIsNone(s.cooldown_until)

    def test_daily_limit_blocks_novice(self):
        c = Coolant()
        s = make_status(daily_count=1)
        self.assertFalse(c.check_submit_allowed(s))

    def test_mature_exempt_from_daily_limit(self):
        c = Coolant()
        s = make_status(stage=Stage.mature, daily_count=10)
        self.assertTrue(c.check_submit_allowed(s))


class TestRecordValidation(unittest.TestCase):

    def test_red_increments_counter(self):
        c = Coolant()
        s = make_status(failures=0)
        c.record_validation(s, "red")
        self.assertEqual(s.consecutive_failures, 1)

    def test_two_consecutive_reds_triggers_cooldown(self):
        c = Coolant()
        s = make_status(failures=1)
        c.record_validation(s, "red")
        self.assertEqual(s.cooldown_state, CooldownState.cooling)
        self.assertIsNotNone(s.cooldown_until)

    def test_green_resets_counter(self):
        c = Coolant()
        s = make_status(failures=2)
        c.record_validation(s, "green")
        self.assertEqual(s.consecutive_failures, 0)

    def test_yellow_resets_counter(self):
        c = Coolant()
        s = make_status(failures=3)
        c.record_validation(s, "yellow")
        self.assertEqual(s.consecutive_failures, 0)


class TestStageThresholds(unittest.TestCase):

    def test_novice_thresholds(self):
        c = Coolant()
        t = c.get_stage_thresholds(Stage.novice)
        self.assertEqual(t["red_upper"], 0.70)

    def test_growing_thresholds(self):
        c = Coolant()
        t = c.get_stage_thresholds(Stage.growing)
        self.assertEqual(t["red_upper"], 0.60)

    def test_mature_no_block(self):
        c = Coolant()
        t = c.get_stage_thresholds(Stage.mature)
        self.assertEqual(t["red_upper"], 1.00)


if __name__ == "__main__":
    unittest.main()
