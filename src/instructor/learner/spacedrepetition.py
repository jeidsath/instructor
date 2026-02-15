"""SM-2 spaced repetition algorithm for vocabulary retention.

Implements the SuperMemo SM-2 algorithm to schedule vocabulary reviews.
After each review, the learner's recall quality (0-5) determines whether
the interval grows (successful recall) or resets (failed recall).
"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instructor.models.vocabulary import LearnerVocabulary

MIN_EASE_FACTOR: float = 1.3
DEFAULT_EASE_FACTOR: float = 2.5
MAX_INTERVAL_DAYS: float = 365.0
FAST_RESPONSE_MS: int = 3000


def update_review(
    item: LearnerVocabulary,
    quality: int,
    *,
    now: datetime | None = None,
) -> LearnerVocabulary:
    """Apply one SM-2 review to a learner vocabulary item.

    Args:
        item: The learner vocabulary record to update (modified in place).
        quality: Recall quality rating, 0-5.
        now: Current time. Defaults to UTC now.

    Returns:
        The same item, updated in place.

    Raises:
        ValueError: If quality is not in 0-5.
    """
    if not 0 <= quality <= 5:
        msg = f"quality must be 0-5, got {quality}"
        raise ValueError(msg)

    if now is None:
        now = datetime.now(UTC)

    # Update ease factor (always, regardless of success/failure).
    item.ease_factor = max(
        MIN_EASE_FACTOR,
        item.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )

    if quality >= 3:
        # Successful recall — grow the interval.
        if item.repetition_count == 0:
            item.interval_days = 1.0
        elif item.repetition_count == 1:
            item.interval_days = 6.0
        else:
            item.interval_days = min(
                item.interval_days * item.ease_factor, MAX_INTERVAL_DAYS
            )
        item.repetition_count += 1
        item.times_correct += 1
    else:
        # Failed recall — reset.
        item.interval_days = 1.0
        item.repetition_count = 0
        item.times_incorrect += 1

    item.strength = 1.0
    item.last_reviewed = now
    item.next_review = now + timedelta(days=item.interval_days)

    return item


def compute_strength(
    item: LearnerVocabulary,
    *,
    now: datetime | None = None,
) -> float:
    """Compute current recall probability for a vocabulary item.

    Uses exponential decay: strength halves every ``interval_days`` since
    the last review. Returns 0.0 if the item has never been reviewed or
    has a zero interval.

    Args:
        item: The learner vocabulary record.
        now: Current time. Defaults to UTC now.

    Returns:
        Recall probability in [0.0, 1.0].
    """
    if item.last_reviewed is None or item.interval_days <= 0:
        return 0.0

    if now is None:
        now = datetime.now(UTC)

    elapsed_days = (now - item.last_reviewed).total_seconds() / 86400.0
    if elapsed_days <= 0:
        return min(1.0, item.strength)

    # Half-life model: strength = 2^(-elapsed / interval)
    exponent = -math.log(2) * elapsed_days / item.interval_days
    return max(0.0, min(1.0, math.exp(exponent)))


def quality_from_response(
    *,
    correct: bool,
    response_time_ms: int,
    hint_used: bool,
) -> int:
    """Map an exercise outcome to an SM-2 quality rating (0-5).

    Mapping:
        - correct, fast (<=3s), no hint → 5
        - correct, slow (>3s), no hint  → 4
        - correct, hint used            → 3
        - incorrect, no hint            → 2
        - incorrect, hint used          → 1

    Args:
        correct: Whether the response was correct.
        response_time_ms: Time to respond in milliseconds.
        hint_used: Whether the learner used a hint.

    Returns:
        Quality rating 1-5.
    """
    if correct:
        if hint_used:
            return 3
        return 5 if response_time_ms <= FAST_RESPONSE_MS else 4
    return 1 if hint_used else 2
