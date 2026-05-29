"""
service.py — ValidationService facade.
Deep seam: one public method, delegates to comparators + aggregator.
"""
from models.schemas import SimilarityInput, SimilarityOutput
from .validation.comparators import SkeletonComparator, EmotionComparator, EmbeddingComparator
from .validation.aggregator import ValidationAggregator


class ValidationService:
    """Public facade. Only import callers need."""

    def __init__(self, skeleton=None, emotion=None, embedding=None):
        self._aggregator = ValidationAggregator(
            skeleton or SkeletonComparator(),
            emotion or EmotionComparator(),
            embedding or EmbeddingComparator(),
        )

    def check(self, req: SimilarityInput) -> SimilarityOutput:
        """
        Single public method.
        No cooldown fields in output — rule-engine decides that.
        """
        return self._aggregator.evaluate(req)
