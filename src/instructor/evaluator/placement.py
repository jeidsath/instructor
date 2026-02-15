"""Placement assessment for new learners.

Determines a learner's starting level by probing vocabulary, grammar,
and reading comprehension across difficulty levels.  Maps the combined
score to a starting curriculum unit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class StartingLevel(IntEnum):
    """Maps score ranges to curriculum starting positions."""

    ABSOLUTE_BEGINNER = 1  # 0–10%
    SOME_EXPOSURE = 2  # 10–30%
    INTERMEDIATE = 4  # 30–60%
    ADVANCED = 7  # 60–80%
    FLUENT = 9  # 80%+


@dataclass(frozen=True, slots=True)
class PlacementResult:
    """Outcome of a placement test."""

    total_score: float  # 0.0 – 1.0
    vocabulary_score: float
    grammar_score: float
    reading_score: float
    starting_unit: int
    demonstrated_vocabulary: list[str] = field(default_factory=list)
    demonstrated_grammar: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PlacementResponse:
    """A single response in a placement test."""

    probe_type: str  # "vocabulary", "grammar", "reading", "alphabet"
    difficulty: int
    correct: bool
    item_id: str = ""  # lemma or concept name


def score_to_starting_unit(score: float) -> int:
    """Map a normalized score (0.0–1.0) to a starting curriculum unit."""
    if score >= 0.80:
        return StartingLevel.FLUENT
    if score >= 0.60:
        return StartingLevel.ADVANCED
    if score >= 0.30:
        return StartingLevel.INTERMEDIATE
    if score >= 0.10:
        return StartingLevel.SOME_EXPOSURE
    return StartingLevel.ABSOLUTE_BEGINNER


def score_placement(responses: list[PlacementResponse]) -> PlacementResult:
    """Analyze placement test responses and determine starting level.

    Computes per-category scores and an overall score, then maps
    to a starting curriculum unit.
    """
    if not responses:
        return PlacementResult(
            total_score=0.0,
            vocabulary_score=0.0,
            grammar_score=0.0,
            reading_score=0.0,
            starting_unit=StartingLevel.ABSOLUTE_BEGINNER,
        )

    vocab_responses = [r for r in responses if r.probe_type == "vocabulary"]
    grammar_responses = [r for r in responses if r.probe_type == "grammar"]
    reading_responses = [r for r in responses if r.probe_type == "reading"]

    vocab_score = _category_score(vocab_responses)
    grammar_score = _category_score(grammar_responses)
    reading_score = _category_score(reading_responses)

    # Weighted average: vocab 40%, grammar 35%, reading 25%
    total = vocab_score * 0.40 + grammar_score * 0.35 + reading_score * 0.25

    demonstrated_vocab = [r.item_id for r in vocab_responses if r.correct and r.item_id]
    demonstrated_grammar = [
        r.item_id for r in grammar_responses if r.correct and r.item_id
    ]

    return PlacementResult(
        total_score=total,
        vocabulary_score=vocab_score,
        grammar_score=grammar_score,
        reading_score=reading_score,
        starting_unit=score_to_starting_unit(total),
        demonstrated_vocabulary=demonstrated_vocab,
        demonstrated_grammar=demonstrated_grammar,
    )


def should_stop_early(responses: list[PlacementResponse]) -> bool:
    """Check whether to terminate the placement test early.

    Stops if the learner has answered incorrectly on all items
    at or below difficulty level 2 (fundamental items).
    """
    basic = [r for r in responses if r.difficulty <= 2]
    if len(basic) < 3:
        return False  # not enough data yet
    return all(not r.correct for r in basic)


def _category_score(responses: list[PlacementResponse]) -> float:
    """Compute score for a category, weighting harder items more."""
    if not responses:
        return 0.0
    weighted_sum = 0.0
    weight_total = 0.0
    for r in responses:
        weight = r.difficulty
        weighted_sum += weight * (1.0 if r.correct else 0.0)
        weight_total += weight
    return weighted_sum / weight_total if weight_total > 0 else 0.0
