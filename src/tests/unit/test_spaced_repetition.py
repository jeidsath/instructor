import uuid
from datetime import UTC, datetime, timedelta

import pytest

from instructor.learner.spacedrepetition import (
    MIN_EASE_FACTOR,
    compute_strength,
    quality_from_response,
    update_review,
)
from instructor.models.vocabulary import LearnerVocabulary


def _make_item(**overrides: object) -> LearnerVocabulary:
    """Create a LearnerVocabulary with sensible defaults for testing."""
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "learner_id": uuid.uuid4(),
        "vocabulary_item_id": uuid.uuid4(),
        "strength": 0.0,
        "ease_factor": 2.5,
        "interval_days": 0.0,
        "repetition_count": 0,
        "last_reviewed": None,
        "next_review": None,
        "times_correct": 0,
        "times_incorrect": 0,
        "knows_definition": False,
        "knows_forms": False,
        "knows_usage": False,
    }
    defaults.update(overrides)
    return LearnerVocabulary(**defaults)


NOW = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)


@pytest.mark.unit
class TestSM2Update:
    """SM-2 algorithm correctly updates review state."""

    def test_first_correct_review_sets_interval_1_day(self) -> None:
        item = _make_item()
        update_review(item, quality=4, now=NOW)
        assert item.interval_days == 1.0
        assert item.repetition_count == 1

    def test_second_correct_review_sets_interval_6_days(self) -> None:
        item = _make_item(repetition_count=1, interval_days=1.0)
        update_review(item, quality=4, now=NOW)
        assert item.interval_days == 6.0
        assert item.repetition_count == 2

    def test_third_correct_review_multiplies_by_ease(self) -> None:
        item = _make_item(repetition_count=2, interval_days=6.0, ease_factor=2.5)
        update_review(item, quality=4, now=NOW)
        assert item.interval_days == pytest.approx(15.0)
        assert item.repetition_count == 3

    def test_failed_review_resets_interval(self) -> None:
        item = _make_item(repetition_count=5, interval_days=30.0, ease_factor=2.5)
        update_review(item, quality=2, now=NOW)
        assert item.interval_days == 1.0
        assert item.repetition_count == 0

    def test_failed_review_decreases_ease(self) -> None:
        item = _make_item(ease_factor=2.5)
        update_review(item, quality=2, now=NOW)
        assert item.ease_factor < 2.5

    def test_high_quality_increases_ease(self) -> None:
        item = _make_item(ease_factor=2.5)
        update_review(item, quality=5, now=NOW)
        assert item.ease_factor > 2.5

    def test_ease_never_below_minimum(self) -> None:
        item = _make_item(ease_factor=MIN_EASE_FACTOR)
        update_review(item, quality=0, now=NOW)
        assert item.ease_factor >= MIN_EASE_FACTOR

    def test_ease_at_minimum_after_many_failures(self) -> None:
        item = _make_item(ease_factor=2.5)
        for _ in range(20):
            update_review(item, quality=0, now=NOW)
        assert item.ease_factor == pytest.approx(MIN_EASE_FACTOR)

    def test_correct_review_increments_times_correct(self) -> None:
        item = _make_item(times_correct=3, times_incorrect=1)
        update_review(item, quality=4, now=NOW)
        assert item.times_correct == 4
        assert item.times_incorrect == 1

    def test_failed_review_increments_times_incorrect(self) -> None:
        item = _make_item(times_correct=3, times_incorrect=1)
        update_review(item, quality=2, now=NOW)
        assert item.times_correct == 3
        assert item.times_incorrect == 2

    def test_strength_set_to_1_after_review(self) -> None:
        item = _make_item(strength=0.3)
        update_review(item, quality=4, now=NOW)
        assert item.strength == 1.0

    def test_last_reviewed_set(self) -> None:
        item = _make_item()
        update_review(item, quality=4, now=NOW)
        assert item.last_reviewed == NOW

    def test_next_review_set(self) -> None:
        item = _make_item()
        update_review(item, quality=4, now=NOW)
        expected = NOW + timedelta(days=1.0)
        assert item.next_review == expected

    def test_quality_must_be_0_to_5(self) -> None:
        item = _make_item()
        with pytest.raises(ValueError, match="quality must be"):
            update_review(item, quality=6, now=NOW)
        with pytest.raises(ValueError, match="quality must be"):
            update_review(item, quality=-1, now=NOW)

    def test_quality_3_is_successful(self) -> None:
        """Quality 3 (correct with difficulty) still counts as successful."""
        item = _make_item()
        update_review(item, quality=3, now=NOW)
        assert item.repetition_count == 1
        assert item.interval_days == 1.0


@pytest.mark.unit
class TestStrengthComputation:
    """Strength (recall probability) decays correctly over time."""

    def test_strength_1_at_review_time(self) -> None:
        item = _make_item(last_reviewed=NOW, interval_days=10.0, strength=1.0)
        assert compute_strength(item, now=NOW) == pytest.approx(1.0)

    def test_strength_half_at_interval(self) -> None:
        item = _make_item(last_reviewed=NOW, interval_days=10.0, strength=1.0)
        later = NOW + timedelta(days=10)
        assert compute_strength(item, now=later) == pytest.approx(0.5)

    def test_strength_quarter_at_double_interval(self) -> None:
        item = _make_item(last_reviewed=NOW, interval_days=10.0, strength=1.0)
        later = NOW + timedelta(days=20)
        assert compute_strength(item, now=later) == pytest.approx(0.25)

    def test_strength_0_when_never_reviewed(self) -> None:
        item = _make_item(last_reviewed=None, interval_days=0.0)
        assert compute_strength(item, now=NOW) == 0.0

    def test_strength_clamped_to_0_1(self) -> None:
        item = _make_item(last_reviewed=NOW, interval_days=1.0, strength=1.0)
        far_future = NOW + timedelta(days=365)
        s = compute_strength(item, now=far_future)
        assert 0.0 <= s <= 1.0

    def test_strength_near_1_shortly_after_review(self) -> None:
        item = _make_item(last_reviewed=NOW, interval_days=10.0, strength=1.0)
        shortly = NOW + timedelta(hours=1)
        s = compute_strength(item, now=shortly)
        assert s > 0.99

    def test_strength_0_when_interval_is_0(self) -> None:
        """Zero interval (never successfully reviewed) returns 0."""
        item = _make_item(last_reviewed=NOW, interval_days=0.0, strength=1.0)
        later = NOW + timedelta(days=1)
        assert compute_strength(item, now=later) == 0.0


@pytest.mark.unit
class TestQualityMapping:
    """Exercise outcomes map to correct SM-2 quality values."""

    def test_correct_fast_returns_5(self) -> None:
        q = quality_from_response(correct=True, response_time_ms=1500, hint_used=False)
        assert q == 5

    def test_correct_slow_returns_4(self) -> None:
        q = quality_from_response(correct=True, response_time_ms=8000, hint_used=False)
        assert q == 4

    def test_correct_with_hint_returns_3(self) -> None:
        q = quality_from_response(correct=True, response_time_ms=2000, hint_used=True)
        assert q == 3

    def test_incorrect_no_hint_returns_2(self) -> None:
        q = quality_from_response(correct=False, response_time_ms=3000, hint_used=False)
        assert q == 2

    def test_incorrect_with_hint_returns_1(self) -> None:
        q = quality_from_response(correct=False, response_time_ms=3000, hint_used=True)
        assert q == 1

    def test_correct_at_threshold_boundary(self) -> None:
        """At exactly 3000ms, should still be fast (quality 5)."""
        q = quality_from_response(correct=True, response_time_ms=3000, hint_used=False)
        assert q == 5

    def test_correct_just_above_threshold(self) -> None:
        q = quality_from_response(correct=True, response_time_ms=3001, hint_used=False)
        assert q == 4


@pytest.mark.unit
class TestSequenceSimulation:
    """Simulate realistic review sequences to verify overall behavior."""

    def test_10_successful_reviews_grow_interval(self) -> None:
        item = _make_item()
        t = NOW
        intervals: list[float] = []
        for _ in range(10):
            update_review(item, quality=5, now=t)
            intervals.append(item.interval_days)
            t += timedelta(days=item.interval_days)

        # Intervals should be non-decreasing, and strictly increasing
        # until they hit the 365-day cap.
        from instructor.learner.spacedrepetition import MAX_INTERVAL_DAYS

        for i in range(2, len(intervals)):
            if intervals[i - 1] < MAX_INTERVAL_DAYS:
                assert intervals[i] > intervals[i - 1], (
                    f"interval[{i}]={intervals[i]} not > "
                    f"interval[{i - 1}]={intervals[i - 1]}"
                )

        # After 10 perfect reviews, interval should have hit the cap
        assert item.interval_days == MAX_INTERVAL_DAYS

    def test_lapse_resets_interval_but_preserves_reasonable_ease(self) -> None:
        """After a lapse, interval resets but ease doesn't crash to minimum."""
        item = _make_item()
        t = NOW

        # 5 successful reviews to build up
        for _ in range(5):
            update_review(item, quality=5, now=t)
            t += timedelta(days=item.interval_days)

        ease_before_lapse = item.ease_factor
        interval_before = item.interval_days

        # One lapse
        update_review(item, quality=1, now=t)

        assert item.interval_days == 1.0
        assert item.repetition_count == 0
        assert item.ease_factor < ease_before_lapse
        assert item.ease_factor > MIN_EASE_FACTOR
        assert interval_before > 10  # was well-established

    def test_alternating_success_failure_keeps_short_interval(self) -> None:
        """Inconsistent responses prevent interval from growing much."""
        item = _make_item()
        t = NOW
        for i in range(10):
            q = 5 if i % 2 == 0 else 1
            update_review(item, quality=q, now=t)
            t += timedelta(days=max(item.interval_days, 0.5))

        # Should not have built up a long interval
        assert item.interval_days <= 6

    def test_ease_factor_converges_with_consistent_quality(self) -> None:
        """Ease factor stabilizes when quality is consistent."""
        item = _make_item()
        t = NOW
        ease_values: list[float] = []
        for _ in range(20):
            update_review(item, quality=4, now=t)
            ease_values.append(item.ease_factor)
            t += timedelta(days=item.interval_days)

        # Last 5 ease values should be very close to each other
        last_five = ease_values[-5:]
        assert max(last_five) - min(last_five) < 0.01
