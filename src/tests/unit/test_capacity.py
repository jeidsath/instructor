import uuid

import pytest

from instructor.learner.capacity import (
    EXERCISE_CAPACITY_MAP,
    K_MAX,
    K_MIN,
    capacity_for_exercise,
    compute_adjustment,
    expected_score,
    k_factor,
    update_capacity,
)
from instructor.models.enums import Language
from instructor.models.learner import LearnerLanguageState

LEARNER_ID = uuid.uuid4()


def _state(**overrides: object) -> LearnerLanguageState:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "learner_id": LEARNER_ID,
        "language": Language.LATIN,
        "reading_level": 5.0,
        "writing_level": 5.0,
        "listening_level": 5.0,
        "speaking_level": 5.0,
        "total_study_time_minutes": 0,
    }
    defaults.update(overrides)
    return LearnerLanguageState(**defaults)


@pytest.mark.unit
class TestExpectedScore:
    """expected_score implements ELO-like probability."""

    def test_equal_level_and_difficulty(self) -> None:
        assert expected_score(5.0, 5.0) == pytest.approx(0.5)

    def test_level_above_difficulty(self) -> None:
        score = expected_score(8.0, 5.0)
        assert score > 0.5
        assert score < 1.0

    def test_level_below_difficulty(self) -> None:
        score = expected_score(2.0, 5.0)
        assert score < 0.5
        assert score > 0.0

    def test_large_gap_high(self) -> None:
        score = expected_score(10.0, 2.0)
        assert score > 0.95

    def test_large_gap_low(self) -> None:
        score = expected_score(2.0, 10.0)
        assert score < 0.05


@pytest.mark.unit
class TestKFactor:
    """k_factor decreases with experience."""

    def test_new_learner(self) -> None:
        assert k_factor(0) == K_MAX

    def test_experienced_learner(self) -> None:
        assert k_factor(50) == K_MIN

    def test_very_experienced(self) -> None:
        assert k_factor(100) == K_MIN

    def test_midpoint(self) -> None:
        k = k_factor(25)
        assert K_MIN < k < K_MAX

    def test_monotonically_decreasing(self) -> None:
        values = [k_factor(i) for i in range(51)]
        for i in range(1, len(values)):
            assert values[i] <= values[i - 1]


@pytest.mark.unit
class TestComputeAdjustment:
    """compute_adjustment returns correct direction and magnitude."""

    def test_correct_on_hard_raises_level(self) -> None:
        adj = compute_adjustment(level=5.0, difficulty=8.0, score=1.0)
        assert adj > 0

    def test_wrong_on_easy_lowers_level(self) -> None:
        adj = compute_adjustment(level=5.0, difficulty=2.0, score=0.0)
        assert adj < 0

    def test_expected_performance_small_adjustment(self) -> None:
        """Performing as expected should produce a near-zero adjustment."""
        exp = expected_score(5.0, 5.0)
        adj = compute_adjustment(level=5.0, difficulty=5.0, score=exp)
        assert abs(adj) < 0.01

    def test_surprise_outperformance_large(self) -> None:
        """Correct on much harder exercise → large positive adjustment."""
        adj_hard = compute_adjustment(level=3.0, difficulty=8.0, score=1.0)
        adj_easy = compute_adjustment(level=3.0, difficulty=3.0, score=1.0)
        assert adj_hard > adj_easy

    def test_k_factor_affects_magnitude(self) -> None:
        adj_new = compute_adjustment(
            level=5.0,
            difficulty=8.0,
            score=1.0,
            total_sessions=0,
        )
        adj_exp = compute_adjustment(
            level=5.0,
            difficulty=8.0,
            score=1.0,
            total_sessions=100,
        )
        assert abs(adj_new) > abs(adj_exp)


@pytest.mark.unit
class TestUpdateCapacity:
    """update_capacity modifies the right field on state."""

    def test_reading_updated(self) -> None:
        state = _state(reading_level=5.0)
        update_capacity(state, "reading", exercise_difficulty=8.0, score=1.0)
        assert state.reading_level > 5.0

    def test_writing_updated(self) -> None:
        state = _state(writing_level=5.0)
        update_capacity(state, "writing", exercise_difficulty=2.0, score=0.0)
        assert state.writing_level < 5.0

    def test_listening_updated(self) -> None:
        state = _state(listening_level=5.0)
        update_capacity(state, "listening", exercise_difficulty=5.0, score=1.0)
        assert state.listening_level >= 5.0

    def test_speaking_updated(self) -> None:
        state = _state(speaking_level=5.0)
        update_capacity(state, "speaking", exercise_difficulty=5.0, score=0.0)
        assert state.speaking_level <= 5.0

    def test_invalid_capacity_raises(self) -> None:
        state = _state()
        with pytest.raises(ValueError, match="Unknown capacity"):
            update_capacity(state, "flying", exercise_difficulty=5.0, score=1.0)

    def test_level_never_negative(self) -> None:
        state = _state(reading_level=0.1)
        update_capacity(state, "reading", exercise_difficulty=10.0, score=0.0)
        assert state.reading_level >= 0.0

    def test_returns_same_state(self) -> None:
        state = _state()
        result = update_capacity(state, "reading", exercise_difficulty=5.0, score=1.0)
        assert result is state


@pytest.mark.unit
class TestCapacityForExercise:
    """capacity_for_exercise maps exercise types."""

    def test_reading_exercises(self) -> None:
        assert capacity_for_exercise("definition_recall") == "reading"
        assert capacity_for_exercise("comprehension") == "reading"

    def test_writing_exercises(self) -> None:
        assert capacity_for_exercise("form_production") == "writing"
        assert capacity_for_exercise("composition") == "writing"

    def test_unknown_returns_none(self) -> None:
        assert capacity_for_exercise("unknown_type") is None

    def test_all_mapped_types_valid(self) -> None:
        valid = {"reading", "writing", "listening", "speaking"}
        for cap in EXERCISE_CAPACITY_MAP.values():
            assert cap in valid
