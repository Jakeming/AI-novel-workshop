"""
coolant.py — Rule engine cooldown / frequency / stage logic.

Single source of truth. AI engine never outputs cooldown fields.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class Stage(str, Enum):
    novice = "novice"
    growing = "growing"
    mature = "mature"


class CooldownState(str, Enum):
    normal = "normal"
    cooling = "cooling"


@dataclass
class UserStatus:
    user_id: str
    stage: Stage
    can_submit_new_imitation: bool
    cooldown_until: datetime | None
    consecutive_failures: int
    daily_submit_count: int
    cooldown_state: CooldownState


class Coolant:
    """
    Deep module: all cooldown/frequency/stage logic in one seam.
    No dependency on AI engine or LLM.
    """

    COOLDOWN_HOURS = 24
    DAILY_SUBMIT_LIMIT = 1
    FAILURE_THRESHOLD = 2  # consecutive failures -> cooldown

    def check_submit_allowed(self, status: UserStatus, now: datetime | None = None) -> bool:
        """
        Can user submit a new imitation draft?
        Checks cooldown + daily limit + stage rules.
        """
        now = now or datetime.utcnow()
        if status.cooldown_state == CooldownState.cooling:
            if status.cooldown_until and now < status.cooldown_until:
                return False
            # cooldown expired — auto-reset
            status.cooldown_state = CooldownState.normal
            status.cooldown_until = None
        if status.stage != Stage.mature and status.daily_submit_count >= self.DAILY_SUBMIT_LIMIT:
            return False
        return True

    def record_validation(self, status: UserStatus, verdict: str) -> UserStatus:
        """
        Update user state after validation result.
        verdict from AI engine: "green" | "yellow" | "red"
        """
        if verdict == "red":
            status.consecutive_failures += 1
            if status.consecutive_failures >= self.FAILURE_THRESHOLD:
                status.cooldown_state = CooldownState.cooling
                status.cooldown_until = datetime.utcnow() + timedelta(hours=self.COOLDOWN_HOURS)
        else:
            status.consecutive_failures = 0  # pass resets counter

        return status

    def get_stage_thresholds(self, stage: Stage) -> dict:
        """Return validation thresholds for current stage."""
        return {
            Stage.novice:  {"red_upper": 0.70, "yellow_upper": 0.30},
            Stage.growing: {"red_upper": 0.60, "yellow_upper": 0.30},
            Stage.mature:  {"red_upper": 1.00, "yellow_upper": 1.00},
        }.get(stage, {"red_upper": 0.70, "yellow_upper": 0.30})
