"""
test_aggregator.py — TDD for ValidationAggregator.
Vertical slices: one behavior per test.
"""
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import importlib
ValidationAggregator = importlib.import_module("validation.aggregator").ValidationAggregator
mod = importlib.import_module("models.schemas")
SimilarityInput = mod.SimilarityInput
Verdict = mod.Verdict
Stage = mod.Stage


class FixedComparator:
    """Dummy comparator returning fixed values."""
    def __init__(self, val: float):
        self._val = val
    def compare(self, a: str, b: str) -> float:
        return self._val


def _make_req(composite: float, stage=Stage.novice, answers=None,
              failures=0, relax=False):
    return SimilarityInput(
        original_text="a", imitation_text="b",
        user_answers=answers or {"conflict_cause": "x", "motivation": "y", "value_core": "z"},
        stage=stage,
        previous_failures=failures,
        allow_threshold_relaxation=relax,
    )


class TestVerdictThresholds(unittest.TestCase):

    def test_red_when_above_70(self):
        agg = ValidationAggregator(
            FixedComparator(0.80), FixedComparator(0.80), FixedComparator(0.0))
        self.assertEqual(agg.evaluate(_make_req(0.80)).verdict, Verdict.red)

    def test_yellow_when_between_30_and_70(self):
        agg = ValidationAggregator(
            FixedComparator(0.50), FixedComparator(0.50), FixedComparator(0.0))
        self.assertEqual(agg.evaluate(_make_req(0.50)).verdict, Verdict.yellow)

    def test_green_when_below_30(self):
        agg = ValidationAggregator(
            FixedComparator(0.20), FixedComparator(0.20), FixedComparator(0.0))
        self.assertEqual(agg.evaluate(_make_req(0.20)).verdict, Verdict.green)

    def test_growing_uses_60_threshold(self):
        agg = ValidationAggregator(
            FixedComparator(0.65), FixedComparator(0.65), FixedComparator(0.0))
        req = _make_req(0.65, stage=Stage.growing)
        self.assertEqual(agg.evaluate(req).verdict, Verdict.red)

    def test_mature_never_blocks(self):
        agg = ValidationAggregator(
            FixedComparator(0.95), FixedComparator(0.95), FixedComparator(0.0))
        req = _make_req(0.95, stage=Stage.mature)
        self.assertEqual(agg.evaluate(req).verdict, Verdict.green)


class TestAnswerWarning(unittest.TestCase):

    def test_answer_above_60_triggers_warning(self):
        agg = ValidationAggregator(
            FixedComparator(0.5), FixedComparator(0.0), FixedComparator(0.9))
        out = agg.evaluate(_make_req(0.0))
        self.assertIn("conflict_cause_similarity > 0.6", out.warnings)
        self.assertEqual(out.verdict, Verdict.yellow)


class TestSkeletonHardRule(unittest.TestCase):

    def test_low_skeleton_suppresses_warning_yellow(self):
        """skeleton < 0.3 -> ignore warning -> fall through to green"""
        agg = ValidationAggregator(
            FixedComparator(0.2), FixedComparator(0.0), FixedComparator(0.9))
        out = agg.evaluate(_make_req(0.12))
        self.assertEqual(out.verdict, Verdict.green)


class TestThresholdRelaxation(unittest.TestCase):

    def test_relaxation_shifts_red_boundary(self):
        """3+ failures + allowance -> threshold +10% -> 0.75 becomes yellow"""
        agg = ValidationAggregator(
            FixedComparator(0.75), FixedComparator(0.75), FixedComparator(0.0))
        out = agg.evaluate(_make_req(0.75, failures=3, relax=True))
        self.assertEqual(out.verdict, Verdict.yellow)


if __name__ == "__main__":
    unittest.main()
