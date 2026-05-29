"""
context.py — Probe context module (Candidate 4).

One-shot load of all data needed by all 8 probes per cycle.
New probes don't touch DB — just read context.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ProbeContext:
    """Aggregated snapshot for one monitoring cycle."""
    snapshot_time: datetime

    # user-level aggregations
    user_id: str
    recent_submissions: list[dict] = field(default_factory=list)   # last 2h
    consecutive_failures_2h: int = 0
    imitation_similarities: list[float] = field(default_factory=list)
    draft_inter_similarity: float = 0.0  # between recent drafts

    # inspiration library
    inspiration_entries: list[dict] = field(default_factory=list)
    inspiration_note_quality: float = 1.0  # avg similarity score

    # skeleton library
    skeleton_topology_count: int = 0
    skeleton_topology_clusters: list[str] = field(default_factory=list)

    # rate tracking
    api_call_count_10m: int = 0
    all_red_or_yellow_10m: bool = False

    # offline mode
    consecutive_drop_count: int = 0

    # plagiarism check
    imitation_text: str = ""
    network_match_ratio: float = 0.0


class ProbeContextLoader:
    """
    Batch-loads all data for one probe cycle.
    Interface: load(user_id) -> ProbeContext
    """

    def __init__(self, db):
        self._db = db

    def load(self, user_id: str) -> ProbeContext:
        """Single round-trip to DB (or batch query) to build context."""
        # In production: one big query joining users, sessions, drafts.
        # Here: placeholder returning empty context.
        ctx = ProbeContext(snapshot_time=datetime.utcnow(), user_id=user_id)
        # _populate(ctx)  — real impl
        return ctx


# --- Probe template — each probe receives context, returns alert or None ---

@dataclass
class Alert:
    probe: str
    severity: str  # info | warn | critical
    message: str


class BaseProbe:
    """All 8 probes inherit from this."""
    name = "base"

    def run(self, ctx: ProbeContext) -> Alert | None:
        raise NotImplementedError


class RejectionLoopProbe(BaseProbe):
    name = "rejection_dead_loop"

    def run(self, ctx: ProbeContext) -> Alert | None:
        if ctx.consecutive_failures_2h >= 3:
            return Alert(self.name, "warn", f"User {ctx.user_id}: ≥3 failures in 2h, auto-relaxed threshold")
        return None


class InspirationPollutionProbe(BaseProbe):
    name = "inspiration_pollution"

    def run(self, ctx: ProbeContext) -> Alert | None:
        if not ctx.inspiration_entries:
            return None
        low_quality = sum(1 for e in ctx.inspiration_entries if e.get("score", 1) < 0.5)
        if low_quality / len(ctx.inspiration_entries) > 0.3:
            return Alert(self.name, "info", "Inspiration library health check recommended")
        return None


class SkeletonDiversityProbe(BaseProbe):
    name = "skeleton_diversity"

    def run(self, ctx: ProbeContext) -> Alert | None:
        if ctx.skeleton_topology_count < 4:
            return Alert(self.name, "info", f"Only {ctx.skeleton_topology_count} topology types — add more")
        return None


class AbuseProbe(BaseProbe):
    name = "abuse_detection"

    def run(self, ctx: ProbeContext) -> Alert | None:
        if ctx.draft_inter_similarity > 0.8:
            return Alert(self.name, "warn", "Suspected abuse: drafts too similar")
        return None


class RateLimitProbe(BaseProbe):
    name = "rate_limit"

    def run(self, ctx: ProbeContext) -> Alert | None:
        if ctx.api_call_count_10m > 10 and ctx.all_red_or_yellow_10m:
            return Alert(self.name, "critical", "Rate limit + all failures — freezing API")
        return None
