import uuid
from datetime import UTC, datetime, timedelta

import pytest

from instructor.learner.mastery import (
    INACTIVITY_DAYS,
    can_advance,
    check_regression,
    complete_lesson,
    confirm_mastery,
    record_attempt,
)
from instructor.models.enums import MasteryLevel
from instructor.models.grammar import LearnerGrammar


def _make_item(**overrides: object) -> LearnerGrammar:
    """Create a LearnerGrammar with sensible defaults for testing."""
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "learner_id": uuid.uuid4(),
        "grammar_concept_id": uuid.uuid4(),
        "mastery_level": MasteryLevel.UNKNOWN,
        "last_practiced": None,
        "times_practiced": 0,
        "recent_error_rate": 0.0,
    }
    defaults.update(overrides)
    return LearnerGrammar(**defaults)


NOW = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)


@pytest.mark.unit
class TestCompletLesson:
    """Lesson completion advances UNKNOWN → INTRODUCED."""

    def test_unknown_to_introduced(self) -> None:
        item = _make_item(mastery_level=MasteryLevel.UNKNOWN)
        complete_lesson(item)
        assert item.mastery_level == MasteryLevel.INTRODUCED

    def test_already_introduced_is_noop(self) -> None:
        item = _make_item(mastery_level=MasteryLevel.INTRODUCED)
        complete_lesson(item)
        assert item.mastery_level == MasteryLevel.INTRODUCED

    def test_higher_level_is_noop(self) -> None:
        item = _make_item(mastery_level=MasteryLevel.FAMILIAR)
        complete_lesson(item)
        assert item.mastery_level == MasteryLevel.FAMILIAR


@pytest.mark.unit
class TestRecordAttempt:
    """record_attempt updates error rate and auto-advances."""

    def test_introduced_to_practicing_on_first_attempt(self) -> None:
        item = _make_item(mastery_level=MasteryLevel.INTRODUCED)
        record_attempt(item, correct=True, now=NOW)
        assert item.mastery_level == MasteryLevel.PRACTICING
        assert item.times_practiced == 1

    def test_times_practiced_increments(self) -> None:
        item = _make_item(mastery_level=MasteryLevel.PRACTICING, times_practiced=5)
        record_attempt(item, correct=True, now=NOW)
        assert item.times_practiced == 6

    def test_last_practiced_updated(self) -> None:
        item = _make_item(mastery_level=MasteryLevel.PRACTICING)
        record_attempt(item, correct=True, now=NOW)
        assert item.last_practiced == NOW

    def test_error_rate_decreases_on_correct(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.5,
            times_practiced=10,
        )
        record_attempt(item, correct=True, now=NOW)
        assert item.recent_error_rate < 0.5

    def test_error_rate_increases_on_incorrect(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.2,
            times_practiced=10,
        )
        record_attempt(item, correct=False, now=NOW)
        assert item.recent_error_rate > 0.2

    def test_error_rate_stays_in_0_1(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.0,
            times_practiced=10,
        )
        record_attempt(item, correct=True, now=NOW)
        assert 0.0 <= item.recent_error_rate <= 1.0

        item2 = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=1.0,
            times_practiced=10,
        )
        record_attempt(item2, correct=False, now=NOW)
        assert 0.0 <= item2.recent_error_rate <= 1.0

    def test_practicing_to_familiar(self) -> None:
        """Advance when error_rate < 0.40 and times_practiced >= 10."""
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.1,
            times_practiced=9,
        )
        record_attempt(item, correct=True, now=NOW)
        assert item.mastery_level == MasteryLevel.FAMILIAR

    def test_practicing_not_advanced_insufficient_attempts(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.1,
            times_practiced=5,
        )
        record_attempt(item, correct=True, now=NOW)
        assert item.mastery_level == MasteryLevel.PRACTICING

    def test_practicing_not_advanced_high_error_rate(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.5,
            times_practiced=15,
        )
        record_attempt(item, correct=True, now=NOW)
        assert item.mastery_level == MasteryLevel.PRACTICING

    def test_familiar_to_proficient(self) -> None:
        """Advance when error_rate < 0.15 and times_practiced >= 20."""
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            recent_error_rate=0.05,
            times_practiced=19,
        )
        record_attempt(item, correct=True, now=NOW)
        assert item.mastery_level == MasteryLevel.PROFICIENT

    def test_familiar_not_advanced_insufficient_attempts(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            recent_error_rate=0.05,
            times_practiced=15,
        )
        record_attempt(item, correct=True, now=NOW)
        assert item.mastery_level == MasteryLevel.FAMILIAR

    def test_proficient_does_not_auto_advance(self) -> None:
        """PROFICIENT → MASTERED requires AI confirmation, not auto-advance."""
        item = _make_item(
            mastery_level=MasteryLevel.PROFICIENT,
            recent_error_rate=0.01,
            times_practiced=50,
        )
        record_attempt(item, correct=True, now=NOW)
        assert item.mastery_level == MasteryLevel.PROFICIENT

    def test_unknown_gets_no_attempt(self) -> None:
        """Can't practice what you haven't been introduced to."""
        item = _make_item(mastery_level=MasteryLevel.UNKNOWN)
        with pytest.raises(ValueError, match="Cannot record attempt"):
            record_attempt(item, correct=True, now=NOW)


@pytest.mark.unit
class TestConfirmMastery:
    """AI-confirmed mastery advances PROFICIENT → MASTERED."""

    def test_proficient_to_mastered(self) -> None:
        item = _make_item(mastery_level=MasteryLevel.PROFICIENT)
        confirm_mastery(item)
        assert item.mastery_level == MasteryLevel.MASTERED

    def test_not_proficient_raises(self) -> None:
        item = _make_item(mastery_level=MasteryLevel.FAMILIAR)
        with pytest.raises(ValueError, match="must be PROFICIENT"):
            confirm_mastery(item)


@pytest.mark.unit
class TestCanAdvance:
    """can_advance checks readiness for next level."""

    def test_unknown_can_advance(self) -> None:
        """UNKNOWN can always advance (just needs a lesson)."""
        item = _make_item(mastery_level=MasteryLevel.UNKNOWN)
        assert can_advance(item) is True

    def test_introduced_can_advance(self) -> None:
        """INTRODUCED can advance (just needs first attempt)."""
        item = _make_item(mastery_level=MasteryLevel.INTRODUCED)
        assert can_advance(item) is True

    def test_practicing_can_advance_when_ready(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.2,
            times_practiced=12,
        )
        assert can_advance(item) is True

    def test_practicing_cannot_advance_high_errors(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.5,
            times_practiced=12,
        )
        assert can_advance(item) is False

    def test_practicing_cannot_advance_few_attempts(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.1,
            times_practiced=5,
        )
        assert can_advance(item) is False

    def test_familiar_can_advance_when_ready(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            recent_error_rate=0.10,
            times_practiced=25,
        )
        assert can_advance(item) is True

    def test_familiar_cannot_advance_high_errors(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            recent_error_rate=0.20,
            times_practiced=25,
        )
        assert can_advance(item) is False

    def test_mastered_cannot_advance(self) -> None:
        item = _make_item(mastery_level=MasteryLevel.MASTERED)
        assert can_advance(item) is False


@pytest.mark.unit
class TestCheckRegression:
    """Inactivity + high error rate causes level regression."""

    def test_no_regression_when_recently_active(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            recent_error_rate=0.5,
            last_practiced=NOW - timedelta(days=5),
        )
        check_regression(item, now=NOW)
        assert item.mastery_level == MasteryLevel.FAMILIAR

    def test_no_regression_when_error_rate_low(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            recent_error_rate=0.1,
            last_practiced=NOW - timedelta(days=30),
        )
        check_regression(item, now=NOW)
        assert item.mastery_level == MasteryLevel.FAMILIAR

    def test_familiar_regresses_to_practicing(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            recent_error_rate=0.5,
            last_practiced=NOW - timedelta(days=INACTIVITY_DAYS + 1),
        )
        check_regression(item, now=NOW)
        assert item.mastery_level == MasteryLevel.PRACTICING

    def test_proficient_regresses_to_familiar(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.PROFICIENT,
            recent_error_rate=0.20,
            last_practiced=NOW - timedelta(days=INACTIVITY_DAYS + 1),
        )
        check_regression(item, now=NOW)
        assert item.mastery_level == MasteryLevel.FAMILIAR

    def test_mastered_regresses_to_proficient(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.MASTERED,
            recent_error_rate=0.20,
            last_practiced=NOW - timedelta(days=INACTIVITY_DAYS + 1),
        )
        check_regression(item, now=NOW)
        assert item.mastery_level == MasteryLevel.PROFICIENT

    def test_practicing_does_not_regress(self) -> None:
        """PRACTICING and below don't regress further."""
        item = _make_item(
            mastery_level=MasteryLevel.PRACTICING,
            recent_error_rate=0.9,
            last_practiced=NOW - timedelta(days=60),
        )
        check_regression(item, now=NOW)
        assert item.mastery_level == MasteryLevel.PRACTICING

    def test_introduced_does_not_regress(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.INTRODUCED,
            last_practiced=NOW - timedelta(days=60),
        )
        check_regression(item, now=NOW)
        assert item.mastery_level == MasteryLevel.INTRODUCED

    def test_never_practiced_does_not_regress(self) -> None:
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            last_practiced=None,
        )
        check_regression(item, now=NOW)
        assert item.mastery_level == MasteryLevel.FAMILIAR

    def test_regression_at_exact_boundary(self) -> None:
        """At exactly INACTIVITY_DAYS, no regression yet."""
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            recent_error_rate=0.5,
            last_practiced=NOW - timedelta(days=INACTIVITY_DAYS),
        )
        check_regression(item, now=NOW)
        assert item.mastery_level == MasteryLevel.FAMILIAR


@pytest.mark.unit
class TestProgressionSequence:
    """Simulate a full progression through all mastery levels."""

    def test_full_progression(self) -> None:
        item = _make_item()
        t = NOW

        # Use .value comparisons throughout — mastery_level is mutated
        # in-place and mypy's type narrowing from prior assertions would
        # otherwise flag every subsequent comparison as non-overlapping.

        # 0 → 1: lesson
        complete_lesson(item)
        assert item.mastery_level.value == MasteryLevel.INTRODUCED.value

        # 1 → 2: first attempt
        record_attempt(item, correct=True, now=t)
        assert item.mastery_level.value == MasteryLevel.PRACTICING.value

        # 2 → 3: get error rate low with 10+ attempts
        for _ in range(15):
            record_attempt(item, correct=True, now=t)
            t += timedelta(hours=1)
        assert item.mastery_level.value == MasteryLevel.FAMILIAR.value

        # 3 → 4: continue with low error rate, 20+ total
        for _ in range(20):
            record_attempt(item, correct=True, now=t)
            t += timedelta(hours=1)
        assert item.mastery_level.value == MasteryLevel.PROFICIENT.value

        # 4 → 5: AI confirmation
        confirm_mastery(item)
        assert item.mastery_level.value == MasteryLevel.MASTERED.value

    def test_regression_and_recovery(self) -> None:
        """A learner regresses after inactivity then recovers."""
        item = _make_item(
            mastery_level=MasteryLevel.FAMILIAR,
            recent_error_rate=0.35,
            times_practiced=15,
            last_practiced=NOW,
        )

        # Struggle a bit to push error rate up
        t = NOW
        for _ in range(5):
            record_attempt(item, correct=False, now=t)
            t += timedelta(hours=1)

        # Then go inactive
        t += timedelta(days=INACTIVITY_DAYS + 1)
        check_regression(item, now=t)
        assert item.mastery_level.value == MasteryLevel.PRACTICING.value

        # Recover by practicing correctly (not enough to reach PROFICIENT)
        for _ in range(8):
            record_attempt(item, correct=True, now=t)
            t += timedelta(hours=1)
        assert item.mastery_level.value == MasteryLevel.FAMILIAR.value
