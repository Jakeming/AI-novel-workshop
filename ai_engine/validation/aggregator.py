"""
aggregator.py — ValidationAggregator: combines comparators + stage thresholds.
One seam for threshold logic. Changes to pass/fail rules live here only.
"""
from models.schemas import SimilarityInput, SimilarityOutput, Verdict, Stage


class ThresholdTable:
    """Stage-aware thresholds. Single source of truth for pass/fail boundaries."""

    _THRESHOLDS = {
        Stage.novice:  {"red_upper": 0.70, "yellow_upper": 0.30},
        Stage.growing: {"red_upper": 0.60, "yellow_upper": 0.30},
        Stage.mature:  {"red_upper": 1.00, "yellow_upper": 1.00},
    }

    @classmethod
    def for_stage(cls, stage: Stage) -> dict:
        return cls._THRESHOLDS.get(stage, cls._THRESHOLDS[Stage.novice])


class ValidationAggregator:
    """
    Deep module: accepts comparator results, applies thresholds, produces verdict.
    Knows nothing about LLM, DB, or cooldown.
    """

    def __init__(self, skeleton_cmp, emotion_cmp, embedding_cmp):
        self._skeleton = skeleton_cmp
        self._emotion = emotion_cmp
        self._embedding = embedding_cmp

    def evaluate(self, req: SimilarityInput) -> SimilarityOutput:
        stage_t = ThresholdTable.for_stage(req.stage)

        # 1. Run comparators
        skeleton_sim = self._skeleton.compare(req.original_text, req.imitation_text)
        emotion_sim = self._emotion.compare(req.original_text, req.imitation_text)
        composite = 0.6 * skeleton_sim + 0.4 * emotion_sim

        # 2. Check user-answer similarity (hard rule: >0.6 -> yellow)
        warnings = []
        for key in ["conflict_cause", "motivation", "value_core"]:
            ans_sim = self._embedding.compare(
                req.user_answers.get(key, ""),
                req.original_text,
            )
            if ans_sim > 0.6:
                warnings.append(f"{key}_similarity > 0.6")

        # 3. Dynamic threshold relaxation
        red_upper = stage_t["red_upper"]
        yellow_upper = stage_t["yellow_upper"]
        if req.previous_failures >= 3 and req.allow_threshold_relaxation:
            red_upper = min(red_upper * 1.1, 1.0)
            yellow_upper = min(yellow_upper * 1.1, 1.0)

        # 4. Hard rule: skeleton < 0.3 -> clear warning-based yellow
        if skeleton_sim < 0.3:
            warnings = []

        # 5. Composite verdict
        if composite > red_upper:
            verdict = Verdict.red
        elif composite > yellow_upper or warnings:
            verdict = Verdict.yellow
        else:
            verdict = Verdict.green

        return SimilarityOutput(
            conflict_similarity=round(skeleton_sim, 4),
            motivation_similarity=round(composite, 4),
            value_similarity=round(emotion_sim, 4),
            verdict=verdict,
            similar_segments=[],
            warnings=warnings,
        )
