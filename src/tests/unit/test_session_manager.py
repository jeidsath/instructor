import uuid
from datetime import UTC, datetime, timedelta

import pytest

from instructor.learner.model import LearnerModel
from instructor.models.enums import Language, SessionType
from instructor.models.learner import Learner, LearnerLanguageState
from instructor.practice.exercises import GeneratedExercise
from instructor.session.manager import (
    ActivityResult,
    SessionPlan,
    compute_summary,
    plan_session,
    should_adapt_difficulty,
)

NOW = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
LEARNER_ID = uuid.uuid4()


def _model(
    last_session_at: datetime | None = NOW - timedelta(days=1),
) -> LearnerModel:
    return LearnerModel(
        learner=Learner(id=LEARNER_ID, name="Test"),
        language=Language.LATIN,
        state=LearnerLanguageState(
            id=uuid.uuid4(),
            learner_id=LEARNER_ID,
            language=Language.LATIN,
            reading_level=3.0,
            writing_level=2.0,
            listening_level=1.0,
            speaking_level=4.0,
            last_session_at=last_session_at,
        ),
    )


def _exercises(count: int = 5) -> list[GeneratedExercise]:
    return [
        GeneratedExercise(
            exercise_type="definition_recall",
            prompt=f"Question {i}",
            expected_response=f"Answer {i}",
        )
        for i in range(count)
    ]


def _result(index: int, correct: bool = True, time_ms: int = 2000) -> ActivityResult:
    return ActivityResult(
        activity_index=index,
        exercise_type="definition_recall",
        prompt=f"Q{index}",
        response=f"A{index}",
        score=1.0 if correct else 0.0,
        correct=correct,
        feedback="ok",
        time_taken_ms=time_ms,
    )


@pytest.mark.unit
class TestSessionPlan:
    """SessionPlan tracks exercise progress."""

    def test_initial_state(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(3),
            started_at=NOW,
        )
        assert plan.current_index == 0
        assert plan.is_complete is False

    def test_next_exercise(self) -> None:
        exs = _exercises(3)
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=exs,
            started_at=NOW,
        )
        assert plan.next_exercise() is exs[0]

    def test_record_advances_index(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(3),
            started_at=NOW,
        )
        plan.record_result(_result(0))
        assert plan.current_index == 1

    def test_complete_after_all_answered(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(2),
            started_at=NOW,
        )
        plan.record_result(_result(0))
        plan.record_result(_result(1))
        assert plan.is_complete is True
        assert plan.next_exercise() is None

    def test_empty_exercises(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=[],
            started_at=NOW,
        )
        assert plan.is_complete is True
        assert plan.next_exercise() is None


@pytest.mark.unit
class TestPlanSession:
    """plan_session determines session type from model."""

    def test_practice_session(self) -> None:
        model = _model()
        plan = plan_session(model, _exercises(), now=NOW)
        assert plan.session_type == SessionType.PRACTICE

    def test_placement_for_new_learner(self) -> None:
        model = _model(last_session_at=None)
        plan = plan_session(model, _exercises(), now=NOW)
        assert plan.session_type == SessionType.PLACEMENT

    def test_exercises_preserved(self) -> None:
        exs = _exercises(3)
        model = _model()
        plan = plan_session(model, exs, now=NOW)
        assert plan.exercises == exs

    def test_started_at_set(self) -> None:
        model = _model()
        plan = plan_session(model, _exercises(), now=NOW)
        assert plan.started_at == NOW


@pytest.mark.unit
class TestComputeSummary:
    """compute_summary computes correct statistics."""

    def test_all_correct(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(3),
            started_at=NOW,
        )
        for i in range(3):
            plan.record_result(_result(i, correct=True, time_ms=1000))
        summary = compute_summary(plan)
        assert summary.accuracy == 1.0
        assert summary.correct_count == 3
        assert summary.incorrect_count == 0
        assert summary.average_time_ms == 1000.0

    def test_mixed_results(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(4),
            started_at=NOW,
        )
        plan.record_result(_result(0, correct=True))
        plan.record_result(_result(1, correct=False))
        plan.record_result(_result(2, correct=True))
        plan.record_result(_result(3, correct=False))
        summary = compute_summary(plan)
        assert summary.accuracy == 0.5
        assert summary.correct_count == 2
        assert summary.incorrect_count == 2

    def test_empty_session(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=[],
            started_at=NOW,
        )
        summary = compute_summary(plan)
        assert summary.accuracy == 0.0
        assert summary.total_activities == 0

    def test_session_type_preserved(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.LESSON,
            exercises=[],
            started_at=NOW,
        )
        summary = compute_summary(plan)
        assert summary.session_type == SessionType.LESSON


@pytest.mark.unit
class TestShouldAdaptDifficulty:
    """should_adapt_difficulty checks recent performance."""

    def test_no_results_same(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(5),
            started_at=NOW,
        )
        assert should_adapt_difficulty(plan) == "same"

    def test_all_wrong_easier(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(5),
            started_at=NOW,
        )
        for i in range(3):
            plan.record_result(_result(i, correct=False))
        assert should_adapt_difficulty(plan) == "easier"

    def test_all_correct_5_harder(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(10),
            started_at=NOW,
        )
        for i in range(5):
            plan.record_result(_result(i, correct=True))
        assert should_adapt_difficulty(plan) == "harder"

    def test_mixed_same(self) -> None:
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(5),
            started_at=NOW,
        )
        plan.record_result(_result(0, correct=True))
        plan.record_result(_result(1, correct=False))
        plan.record_result(_result(2, correct=True))
        assert should_adapt_difficulty(plan) == "same"

    def test_only_looks_at_last_5(self) -> None:
        """Even if early results were bad, recent good ones → harder."""
        plan = SessionPlan(
            session_type=SessionType.PRACTICE,
            exercises=_exercises(10),
            started_at=NOW,
        )
        # 3 wrong, then 5 right
        for i in range(3):
            plan.record_result(_result(i, correct=False))
        for i in range(3, 8):
            plan.record_result(_result(i, correct=True))
        assert should_adapt_difficulty(plan) == "harder"
