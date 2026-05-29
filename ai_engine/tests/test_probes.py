"""
test_probes.py — TDD for Guard-AI probes.
Vertical slices: one trigger condition per test.
"""
import sys, os, unittest
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import importlib
mod = importlib.import_module("probe.context")
ProbeContext = mod.ProbeContext
Alert = mod.Alert
RejectionLoopProbe = mod.RejectionLoopProbe
InspirationPollutionProbe = mod.InspirationPollutionProbe
SkeletonDiversityProbe = mod.SkeletonDiversityProbe
AbuseProbe = mod.AbuseProbe
RateLimitProbe = mod.RateLimitProbe


def ctx(**kw):
    defaults = dict(user_id="t1", snapshot_time=datetime.utcnow())
    defaults.update(kw)
    return ProbeContext(**defaults)


class TestRejectionLoopProbe(unittest.TestCase):

    def test_3_failures_triggers_warning(self):
        p = RejectionLoopProbe()
        c = ctx(consecutive_failures_2h=3)
        alert = p.run(c)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "warn")
        self.assertIn("t1", alert.message)

    def test_0_failures_returns_none(self):
        p = RejectionLoopProbe()
        self.assertIsNone(p.run(ctx(consecutive_failures_2h=0)))

    def test_2_failures_returns_none(self):
        p = RejectionLoopProbe()
        self.assertIsNone(p.run(ctx(consecutive_failures_2h=2)))


class TestInspirationPollutionProbe(unittest.TestCase):

    def test_high_pollution_triggers_info(self):
        p = InspirationPollutionProbe()
        c = ctx(inspiration_entries=[
            {"score": 0.1}, {"score": 0.2}, {"score": 0.9}
        ])
        alert = p.run(c)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "info")

    def test_empty_entries_returns_none(self):
        p = InspirationPollutionProbe()
        self.assertIsNone(p.run(ctx(inspiration_entries=[])))

    def test_clean_entries_returns_none(self):
        p = InspirationPollutionProbe()
        c = ctx(inspiration_entries=[
            {"score": 0.9}, {"score": 0.8}, {"score": 0.95}
        ])
        self.assertIsNone(p.run(c))


class TestSkeletonDiversityProbe(unittest.TestCase):

    def test_less_than_4_topologies_triggers_info(self):
        p = SkeletonDiversityProbe()
        self.assertIsNotNone(p.run(ctx(skeleton_topology_count=3)))

    def test_4_or_more_returns_none(self):
        p = SkeletonDiversityProbe()
        self.assertIsNone(p.run(ctx(skeleton_topology_count=4)))
        self.assertIsNone(p.run(ctx(skeleton_topology_count=10)))

    def test_zero_topologies_triggers_info(self):
        p = SkeletonDiversityProbe()
        self.assertIsNotNone(p.run(ctx(skeleton_topology_count=0)))


class TestAbuseProbe(unittest.TestCase):

    def test_high_similarity_triggers_warning(self):
        p = AbuseProbe()
        alert = p.run(ctx(draft_inter_similarity=0.9))
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "warn")

    def test_low_similarity_returns_none(self):
        p = AbuseProbe()
        self.assertIsNone(p.run(ctx(draft_inter_similarity=0.5)))

    def test_edge_80_returns_none(self):
        """Border: exactly 0.80 should NOT trigger (threshold is > 0.8)."""
        p = AbuseProbe()
        self.assertIsNone(p.run(ctx(draft_inter_similarity=0.8)))


class TestRateLimitProbe(unittest.TestCase):

    def test_high_calls_plus_all_failures_triggers_critical(self):
        p = RateLimitProbe()
        alert = p.run(ctx(api_call_count_10m=15, all_red_or_yellow_10m=True))
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "critical")

    def test_high_calls_no_failures_returns_none(self):
        p = RateLimitProbe()
        self.assertIsNone(p.run(ctx(api_call_count_10m=15, all_red_or_yellow_10m=False)))

    def test_low_calls_returns_none(self):
        p = RateLimitProbe()
        self.assertIsNone(p.run(ctx(api_call_count_10m=5, all_red_or_yellow_10m=True)))


if __name__ == "__main__":
    unittest.main()
