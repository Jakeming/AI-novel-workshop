"""
schemas.py — Shared data models for all AI tasks.
One source of truth for I/O shapes.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Stage(str, Enum):
    novice = "novice"
    growing = "growing"
    mature = "mature"


class Verdict(str, Enum):
    green = "green"
    yellow = "yellow"
    red = "red"


# --- AI task outputs ---

@dataclass
class DeepReadOutput:
    summary: str
    emotion_curve: list[dict]          # [{"position": int, "valence": float, "arousal": float}]
    hooks: list[dict]                  # [{"position": int, "type": str}]
    paragraph_functions: list[dict]    # [{"start": int, "end": int, "function": str}]


@dataclass
class DeconstructOutput:
    intent: str
    structure: str
    plot: list[str]
    language: str
    portable_logic: list[str]
    specific_elements: list[str]


@dataclass
class SkeletonOutput:
    text_skeleton: str
    mermaid_code: str


@dataclass
class SimilarityInput:
    original_text: str
    imitation_text: str
    user_answers: dict                    # {conflict_cause, motivation, value_core}
    stage: Stage
    previous_failures: int = 0
    allow_threshold_relaxation: bool = False


@dataclass
class SimilarityOutput:
    conflict_similarity: float
    motivation_similarity: float
    value_similarity: float
    verdict: Verdict
    similar_segments: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # NO cooldown fields — that's rule-engine's job


@dataclass
class StripTestOutput:
    original: str
    test_cases: list[dict]               # [{"genre": str, "rewritten": str}]


@dataclass
class ReflectionOutput:
    questions: list[str]


@dataclass
class NarrativeCheckOutput:
    inconsistencies: list[dict]          # [{"type": "critical"|"advisory", "description": str}]
