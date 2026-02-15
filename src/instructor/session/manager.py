"""Session manager: orchestrates learning sessions.

The manager is a pure-logic module that determines session type,
sequences activities, scores responses, and computes summaries.
Database persistence is handled by the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instructor.learner.model import LearnerModel
    from instructor.models.enums import SessionType
    from instructor.practice.exercises import GeneratedExercise

# Default activity counts per session type.
PRACTICE_COUNT: int = 15
LESSON_PRACTICE_COUNT: int = 8
EVALUATION_COUNT: int = 20


@dataclass(slots=True)
class ActivityResult:
    """Outcome of a single activity within a session."""

    activity_index: int
    exercise_type: str
    prompt: str
    response: str
    score: float  # 0.0 – 1.0
    correct: bool
    feedback: str
    time_taken_ms: int = 0


@dataclass(slots=True)
class SessionPlan:
    """A planned session with its type and exercises."""

    session_type: SessionType
    exercises: list[GeneratedExercise] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    results: list[ActivityResult] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        """True when all exercises have been answered."""
        return len(self.results) >= len(self.exercises)

    @property
    def current_index(self) -> int:
        """Index of the next exercise to present."""
        return len(self.results)

    def next_exercise(self) -> GeneratedExercise | None:
        """Return the next exercise, or None if session is complete."""
        if self.is_complete:
            return None
        return self.exercises[self.current_index]

    def record_result(self, result: ActivityResult) -> None:
        """Record a completed activity result."""
        self.results.append(result)


@dataclass(frozen=True, slots=True)
class SessionSummary:
    """Summary statistics for a completed session."""

    session_type: SessionType
    total_activities: int
    correct_count: int
    incorrect_count: int
    accuracy: float  # 0.0 – 1.0
    average_time_ms: float
    started_at: datetime
    ended_at: datetime


def plan_session(
    model: LearnerModel,
    exercises: list[GeneratedExercise],
    *,
    now: datetime | None = None,
) -> SessionPlan:
    """Create a session plan based on the learner model.

    Parameters
    ----------
    model:
        The learner's current state.
    exercises:
        Pre-generated exercises (from adaptive selection).
    now:
        Current time for session type determination.
    """
    session_type = model.recommended_session_type(now=now)
    return SessionPlan(
        session_type=session_type,
        exercises=exercises,
        started_at=now or datetime.now(UTC),
    )


def compute_summary(plan: SessionPlan) -> SessionSummary:
    """Compute summary statistics for a completed session."""
    total = len(plan.results)
    correct = sum(1 for r in plan.results if r.correct)
    total_time = sum(r.time_taken_ms for r in plan.results)

    return SessionSummary(
        session_type=plan.session_type,
        total_activities=total,
        correct_count=correct,
        incorrect_count=total - correct,
        accuracy=correct / total if total > 0 else 0.0,
        average_time_ms=total_time / total if total > 0 else 0.0,
        started_at=plan.started_at,
        ended_at=datetime.now(UTC),
    )


def should_adapt_difficulty(plan: SessionPlan) -> str:
    """Check if difficulty should be adjusted based on recent results.

    Returns "easier", "harder", or "same".
    """
    recent = plan.results[-5:] if len(plan.results) >= 5 else plan.results
    if not recent:
        return "same"

    recent_correct = sum(1 for r in recent if r.correct)

    if recent_correct == 0 and len(recent) >= 3:
        return "easier"
    if recent_correct == len(recent) and len(recent) >= 5:
        return "harder"
    return "same"
