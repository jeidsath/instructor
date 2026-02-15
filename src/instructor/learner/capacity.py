"""ELO-like capacity level tracking for language skills.

Each of the four capacities (reading, writing, listening, speaking)
has a numeric level that is updated after every scored exercise using
an ELO-inspired formula.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instructor.models.learner import LearnerLanguageState

# K factor range: starts high for new learners, decreases with experience.
K_MAX: float = 2.0
K_MIN: float = 0.5
K_DECAY_SESSIONS: int = 50  # K reaches K_MIN after this many sessions

# ELO-like scaling parameter.
SCALING_FACTOR: float = 4.0

# Capacity names and their corresponding model fields.
CAPACITY_FIELDS: dict[str, str] = {
    "reading": "reading_level",
    "writing": "writing_level",
    "listening": "listening_level",
    "speaking": "speaking_level",
}

# Exercise type → capacity mapping.
EXERCISE_CAPACITY_MAP: dict[str, str] = {
    "definition_recall": "reading",
    "definition_recognition": "reading",
    "form_identification": "reading",
    "translation_to_english": "reading",
    "comprehension": "reading",
    "form_production": "writing",
    "fill_blank": "writing",
    "translation_to_target": "writing",
    "composition": "writing",
    "error_correction": "writing",
    "dictation": "listening",
    "oral_comprehension": "listening",
    "pronunciation": "speaking",
    "oral_response": "speaking",
}


def expected_score(level: float, difficulty: float) -> float:
    """ELO expected score: probability of success given level vs difficulty."""
    return 1.0 / (1.0 + math.pow(10.0, (difficulty - level) / SCALING_FACTOR))


def k_factor(total_sessions: int) -> float:
    """K factor that decreases with experience for more stable estimates."""
    if total_sessions >= K_DECAY_SESSIONS:
        return K_MIN
    ratio = total_sessions / K_DECAY_SESSIONS
    return K_MAX - (K_MAX - K_MIN) * ratio


def compute_adjustment(
    level: float,
    difficulty: float,
    score: float,
    total_sessions: int = 0,
) -> float:
    """Compute the level adjustment for a single exercise.

    Parameters
    ----------
    level:
        Current capacity level.
    difficulty:
        Exercise difficulty (same scale as level).
    score:
        Actual performance score (0.0 – 1.0).
    total_sessions:
        Total sessions completed by the learner (affects K factor).
    """
    expected = expected_score(level, difficulty)
    k = k_factor(total_sessions)
    return k * (score - expected)


def update_capacity(
    state: LearnerLanguageState,
    capacity: str,
    exercise_difficulty: float,
    score: float,
) -> LearnerLanguageState:
    """Update a capacity level on the learner state.

    Parameters
    ----------
    state:
        The learner's language state (modified in place).
    capacity:
        One of "reading", "writing", "listening", "speaking".
    exercise_difficulty:
        Difficulty level of the exercise.
    score:
        Actual performance score (0.0 – 1.0).

    Returns
    -------
    The same state object with the capacity level updated.

    Raises
    ------
    ValueError:
        If *capacity* is not a valid capacity name.
    """
    field_name = CAPACITY_FIELDS.get(capacity)
    if field_name is None:
        msg = f"Unknown capacity: {capacity!r}"
        raise ValueError(msg)

    current_level = getattr(state, field_name)
    sessions = getattr(state, "total_study_time_minutes", 0) // 30  # rough proxy
    adjustment = compute_adjustment(current_level, exercise_difficulty, score, sessions)
    new_level = max(0.0, current_level + adjustment)
    setattr(state, field_name, new_level)
    return state


def capacity_for_exercise(exercise_type: str) -> str | None:
    """Return the capacity name for an exercise type, or None."""
    return EXERCISE_CAPACITY_MAP.get(exercise_type)
