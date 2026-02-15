"""Grammar mastery progression system.

Implements a 5-level mastery model for grammar concepts:
  0 UNKNOWN → 1 INTRODUCED → 2 PRACTICING → 3 FAMILIAR → 4 PROFICIENT → 5 MASTERED

Level transitions are governed by error-rate thresholds and minimum
attempt counts. Levels can regress after extended inactivity if the
learner's recent error rate exceeds the maintenance threshold.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instructor.models.grammar import LearnerGrammar

from instructor.models.enums import MasteryLevel

# EMA smoothing factor for error-rate updates.
ERROR_RATE_ALPHA: float = 0.1

# Advancement thresholds: (max_error_rate, min_attempts).
PRACTICING_TO_FAMILIAR: tuple[float, int] = (0.40, 10)
FAMILIAR_TO_PROFICIENT: tuple[float, int] = (0.15, 20)

# Regression thresholds: same error-rate limits as advancement.
# If error_rate >= threshold AND inactive > INACTIVITY_DAYS, regress.
REGRESSION_THRESHOLDS: dict[MasteryLevel, float] = {
    MasteryLevel.FAMILIAR: 0.40,
    MasteryLevel.PROFICIENT: 0.15,
    MasteryLevel.MASTERED: 0.15,
}

INACTIVITY_DAYS: int = 14


def complete_lesson(item: LearnerGrammar) -> LearnerGrammar:
    """Mark a lesson as completed, advancing UNKNOWN → INTRODUCED.

    No-op if the learner is already at INTRODUCED or higher.
    """
    if item.mastery_level == MasteryLevel.UNKNOWN:
        item.mastery_level = MasteryLevel.INTRODUCED
    return item


def record_attempt(
    item: LearnerGrammar,
    correct: bool,
    *,
    now: datetime | None = None,
) -> LearnerGrammar:
    """Record a practice attempt, update error rate, and auto-advance.

    Auto-advances:
        INTRODUCED → PRACTICING (on first attempt)
        PRACTICING → FAMILIAR (error_rate < 0.40, attempts >= 10)
        FAMILIAR → PROFICIENT (error_rate < 0.15, attempts >= 20)

    PROFICIENT → MASTERED requires :func:`confirm_mastery`.

    Args:
        item: The learner grammar record (modified in place).
        correct: Whether the attempt was correct.
        now: Current time.  Defaults to UTC now.

    Raises:
        ValueError: If mastery_level is UNKNOWN (must complete lesson first).
    """
    if item.mastery_level == MasteryLevel.UNKNOWN:
        msg = "Cannot record attempt at UNKNOWN level; complete a lesson first"
        raise ValueError(msg)

    if now is None:
        now = datetime.now(UTC)

    # Update tracking.
    item.times_practiced += 1
    item.last_practiced = now

    # Update error rate via EMA.
    error_value = 0.0 if correct else 1.0
    item.recent_error_rate = (
        1 - ERROR_RATE_ALPHA
    ) * item.recent_error_rate + ERROR_RATE_ALPHA * error_value

    # Auto-advance INTRODUCED → PRACTICING on first attempt.
    if item.mastery_level == MasteryLevel.INTRODUCED:
        item.mastery_level = MasteryLevel.PRACTICING
        return item

    # Check threshold-based advancement.
    _check_advance(item)

    return item


def confirm_mastery(item: LearnerGrammar) -> LearnerGrammar:
    """AI-confirmed mastery, advancing PROFICIENT → MASTERED.

    Raises:
        ValueError: If the learner is not at PROFICIENT level.
    """
    if item.mastery_level != MasteryLevel.PROFICIENT:
        msg = (
            f"Learner must be PROFICIENT to confirm mastery, "
            f"currently {item.mastery_level.name}"
        )
        raise ValueError(msg)
    item.mastery_level = MasteryLevel.MASTERED
    return item


def can_advance(item: LearnerGrammar) -> bool:
    """Check whether the item meets criteria for next-level advancement.

    Returns True for UNKNOWN and INTRODUCED (trivial advancement).
    Returns False for MASTERED (no further levels).
    """
    level = item.mastery_level

    if level == MasteryLevel.MASTERED:
        return False
    if level in (MasteryLevel.UNKNOWN, MasteryLevel.INTRODUCED):
        return True
    if level == MasteryLevel.PRACTICING:
        max_err, min_att = PRACTICING_TO_FAMILIAR
        return item.recent_error_rate < max_err and item.times_practiced >= min_att
    if level == MasteryLevel.FAMILIAR:
        max_err, min_att = FAMILIAR_TO_PROFICIENT
        return item.recent_error_rate < max_err and item.times_practiced >= min_att
    # PROFICIENT: can advance only via AI confirmation.
    return False


def check_regression(
    item: LearnerGrammar,
    *,
    now: datetime | None = None,
) -> LearnerGrammar:
    """Drop one mastery level if inactive too long with high error rate.

    Regression applies only to FAMILIAR, PROFICIENT, and MASTERED.
    Requires both conditions:
      - inactive for more than :data:`INACTIVITY_DAYS`
      - error rate at or above the level's maintenance threshold
    """
    if item.mastery_level.value <= MasteryLevel.PRACTICING.value:
        return item

    if item.last_practiced is None:
        return item

    if now is None:
        now = datetime.now(UTC)

    days_inactive = (now - item.last_practiced).total_seconds() / 86400.0
    if days_inactive <= INACTIVITY_DAYS:
        return item

    threshold = REGRESSION_THRESHOLDS.get(item.mastery_level)
    if threshold is None:
        return item

    if item.recent_error_rate >= threshold:
        item.mastery_level = MasteryLevel(item.mastery_level.value - 1)

    return item


def _check_advance(item: LearnerGrammar) -> None:
    """Auto-advance if thresholds are met (internal helper)."""
    if item.mastery_level == MasteryLevel.PRACTICING:
        max_err, min_att = PRACTICING_TO_FAMILIAR
        if item.recent_error_rate < max_err and item.times_practiced >= min_att:
            item.mastery_level = MasteryLevel.FAMILIAR
    elif item.mastery_level == MasteryLevel.FAMILIAR:
        max_err, min_att = FAMILIAR_TO_PROFICIENT
        if item.recent_error_rate < max_err and item.times_practiced >= min_att:
            item.mastery_level = MasteryLevel.PROFICIENT
