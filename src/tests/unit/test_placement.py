import pytest

from instructor.evaluator.placement import (
    PlacementResponse,
    StartingLevel,
    score_placement,
    score_to_starting_unit,
    should_stop_early,
)


@pytest.mark.unit
class TestScoreToStartingUnit:
    """score_to_starting_unit maps score ranges correctly."""

    def test_zero_score(self) -> None:
        assert score_to_starting_unit(0.0) == StartingLevel.ABSOLUTE_BEGINNER

    def test_below_10(self) -> None:
        assert score_to_starting_unit(0.05) == StartingLevel.ABSOLUTE_BEGINNER

    def test_at_10(self) -> None:
        assert score_to_starting_unit(0.10) == StartingLevel.SOME_EXPOSURE

    def test_at_30(self) -> None:
        assert score_to_starting_unit(0.30) == StartingLevel.INTERMEDIATE

    def test_at_60(self) -> None:
        assert score_to_starting_unit(0.60) == StartingLevel.ADVANCED

    def test_at_80(self) -> None:
        assert score_to_starting_unit(0.80) == StartingLevel.FLUENT

    def test_perfect_score(self) -> None:
        assert score_to_starting_unit(1.0) == StartingLevel.FLUENT

    def test_boundary_just_below_30(self) -> None:
        assert score_to_starting_unit(0.29) == StartingLevel.SOME_EXPOSURE


@pytest.mark.unit
class TestScorePlacement:
    """score_placement computes weighted scores and maps to unit."""

    def test_empty_responses(self) -> None:
        result = score_placement([])
        assert result.total_score == 0.0
        assert result.starting_unit == StartingLevel.ABSOLUTE_BEGINNER

    def test_all_correct_easy(self) -> None:
        responses = [
            PlacementResponse("vocabulary", difficulty=1, correct=True, item_id="amō"),
            PlacementResponse("vocabulary", difficulty=2, correct=True, item_id="sum"),
            PlacementResponse(
                "grammar",
                difficulty=1,
                correct=True,
                item_id="1st_decl",
            ),
            PlacementResponse("reading", difficulty=1, correct=True),
        ]
        result = score_placement(responses)
        assert result.total_score == 1.0
        assert result.vocabulary_score == 1.0
        assert result.grammar_score == 1.0

    def test_all_incorrect(self) -> None:
        responses = [
            PlacementResponse("vocabulary", difficulty=1, correct=False),
            PlacementResponse("grammar", difficulty=1, correct=False),
            PlacementResponse("reading", difficulty=1, correct=False),
        ]
        result = score_placement(responses)
        assert result.total_score == 0.0
        assert result.starting_unit == StartingLevel.ABSOLUTE_BEGINNER

    def test_mixed_scores(self) -> None:
        responses = [
            PlacementResponse("vocabulary", difficulty=1, correct=True, item_id="a"),
            PlacementResponse("vocabulary", difficulty=5, correct=False),
            PlacementResponse("grammar", difficulty=1, correct=True, item_id="g1"),
            PlacementResponse("grammar", difficulty=3, correct=False),
        ]
        result = score_placement(responses)
        assert 0.0 < result.total_score < 1.0

    def test_demonstrated_vocabulary_tracked(self) -> None:
        responses = [
            PlacementResponse("vocabulary", difficulty=1, correct=True, item_id="amō"),
            PlacementResponse("vocabulary", difficulty=2, correct=False, item_id="sum"),
        ]
        result = score_placement(responses)
        assert "amō" in result.demonstrated_vocabulary
        assert "sum" not in result.demonstrated_vocabulary

    def test_demonstrated_grammar_tracked(self) -> None:
        responses = [
            PlacementResponse(
                "grammar",
                difficulty=1,
                correct=True,
                item_id="1st_decl",
            ),
            PlacementResponse(
                "grammar",
                difficulty=3,
                correct=False,
                item_id="3rd_decl",
            ),
        ]
        result = score_placement(responses)
        assert "1st_decl" in result.demonstrated_grammar
        assert "3rd_decl" not in result.demonstrated_grammar

    def test_higher_difficulty_weighted_more(self) -> None:
        """Getting hard items right should score higher than easy items."""
        easy_correct = [
            PlacementResponse("vocabulary", difficulty=1, correct=True),
            PlacementResponse("vocabulary", difficulty=1, correct=True),
        ]
        hard_correct = [
            PlacementResponse("vocabulary", difficulty=10, correct=True),
            PlacementResponse("vocabulary", difficulty=1, correct=False),
        ]
        r1 = score_placement(easy_correct)
        r2 = score_placement(hard_correct)
        # Hard correct should outweigh easy correct in weighted scoring
        assert r2.vocabulary_score > r1.vocabulary_score * 0.5

    def test_only_vocab_responses(self) -> None:
        """When only vocab responses exist, grammar/reading default to 0."""
        responses = [
            PlacementResponse("vocabulary", difficulty=1, correct=True, item_id="a"),
        ]
        result = score_placement(responses)
        assert result.grammar_score == 0.0
        assert result.reading_score == 0.0
        # total = 1.0 * 0.40 + 0 * 0.35 + 0 * 0.25 = 0.40
        assert result.total_score == pytest.approx(0.40)


@pytest.mark.unit
class TestShouldStopEarly:
    """should_stop_early terminates when basics are all wrong."""

    def test_not_enough_data(self) -> None:
        responses = [
            PlacementResponse("vocabulary", difficulty=1, correct=False),
        ]
        assert should_stop_early(responses) is False

    def test_all_basic_wrong(self) -> None:
        responses = [
            PlacementResponse("vocabulary", difficulty=1, correct=False),
            PlacementResponse("vocabulary", difficulty=2, correct=False),
            PlacementResponse("grammar", difficulty=1, correct=False),
        ]
        assert should_stop_early(responses) is True

    def test_one_basic_correct(self) -> None:
        responses = [
            PlacementResponse("vocabulary", difficulty=1, correct=True),
            PlacementResponse("vocabulary", difficulty=2, correct=False),
            PlacementResponse("grammar", difficulty=1, correct=False),
        ]
        assert should_stop_early(responses) is False

    def test_high_difficulty_ignored(self) -> None:
        """Only checks items at difficulty <= 2."""
        responses = [
            PlacementResponse("vocabulary", difficulty=1, correct=False),
            PlacementResponse("vocabulary", difficulty=2, correct=False),
            PlacementResponse("grammar", difficulty=2, correct=False),
            PlacementResponse("grammar", difficulty=5, correct=True),  # ignored
        ]
        assert should_stop_early(responses) is True

    def test_empty_responses(self) -> None:
        assert should_stop_early([]) is False
