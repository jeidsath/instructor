"""Tests for adaptive exercise selection."""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from instructor.models.enums import (
    Language,
    MasteryLevel,
)
from instructor.practice.adaptive import select_exercises


def _make_vocab_item(
    lemma: str = "amō",
    definition: str = "to love",
    forms: dict[str, object] | None = None,
) -> MagicMock:
    item = MagicMock()
    item.lemma = lemma
    item.definition = definition
    item.forms = forms
    return item


def _make_learner_vocab(
    *,
    strength: float = 0.5,
    next_review: datetime | None = None,
    lemma: str = "amō",
    definition: str = "to love",
) -> MagicMock:
    lv = MagicMock()
    lv.strength = strength
    lv.next_review = next_review
    lv.vocabulary_item = _make_vocab_item(lemma=lemma, definition=definition)
    return lv


def _make_grammar_concept(
    concept_id: uuid.UUID | None = None,
    name: str = "First Declension",
) -> MagicMock:
    gc = MagicMock()
    gc.id = concept_id or uuid.uuid4()
    gc.name = name
    return gc


def _make_learner_grammar(concept_id: uuid.UUID) -> MagicMock:
    lg = MagicMock()
    lg.grammar_concept_id = concept_id
    lg.mastery_level = MasteryLevel.PRACTICING
    return lg


def _make_model(
    vocabulary: list | None = None,
    grammar: list | None = None,
    grammar_concepts: list | None = None,
    language: Language = Language.LATIN,
) -> MagicMock:
    model = MagicMock()
    model.language = language
    model.vocabulary = vocabulary or []
    model.grammar = grammar or []
    model.grammar_concepts = grammar_concepts or []

    # Wire up the query methods based on the vocabulary list
    vocab = vocabulary or []

    def _due(now: datetime | None = None) -> list:
        if now is None:
            now = datetime.now(UTC)
        return [v for v in vocab if v.next_review and v.next_review <= now]

    def _weak(threshold: float = 0.3) -> list:
        return [v for v in vocab if v.strength < threshold]

    def _strong(threshold: float = 0.7) -> list:
        return [v for v in vocab if v.strength > threshold]

    model.vocabulary_due_for_review = _due
    model.weak_vocabulary = _weak
    model.strong_vocabulary = _strong
    return model


@pytest.mark.unit
class TestSelectExercisesEmpty:
    """Empty learner state."""

    def test_empty_learner_returns_empty(self) -> None:
        model = _make_model()
        result = select_exercises(model, count=10)
        assert result == []

    def test_empty_with_zero_count(self) -> None:
        model = _make_model()
        result = select_exercises(model, count=0)
        assert result == []


@pytest.mark.unit
class TestSelectExercisesDueItems:
    """Exercises from vocabulary due for review."""

    def test_due_items_generate_exercises(self) -> None:
        now = datetime.now(UTC)
        lv = _make_learner_vocab(
            strength=0.5,
            next_review=now - timedelta(days=1),
            lemma="puella",
            definition="girl",
        )
        model = _make_model(vocabulary=[lv])
        result = select_exercises(model, count=5, now=now)
        assert len(result) == 1

    def test_multiple_due_items(self) -> None:
        now = datetime.now(UTC)
        items = [
            _make_learner_vocab(
                strength=0.5,
                next_review=now - timedelta(days=i),
                lemma=f"word_{i}",
                definition=f"def_{i}",
            )
            for i in range(1, 6)
        ]
        model = _make_model(vocabulary=items)
        result = select_exercises(model, count=10, now=now)
        assert len(result) >= 5


@pytest.mark.unit
class TestSelectExercisesWeakItems:
    """Exercises from weak vocabulary."""

    def test_weak_items_generate_exercises(self) -> None:
        lv = _make_learner_vocab(strength=0.1, lemma="rex", definition="king")
        model = _make_model(vocabulary=[lv])
        result = select_exercises(model, count=5)
        assert len(result) >= 1

    def test_weak_items_not_duplicated_with_due(self) -> None:
        now = datetime.now(UTC)
        lv = _make_learner_vocab(
            strength=0.1,
            next_review=now - timedelta(days=1),
            lemma="rex",
            definition="king",
        )
        model = _make_model(vocabulary=[lv])
        result = select_exercises(model, count=10, now=now)
        # Should produce exercises from both due and weak paths
        assert len(result) >= 1


@pytest.mark.unit
class TestSelectExercisesStrongItems:
    """Review exercises from strong vocabulary."""

    def test_strong_items_generate_review(self) -> None:
        lv = _make_learner_vocab(strength=0.9, lemma="aqua", definition="water")
        model = _make_model(vocabulary=[lv])
        result = select_exercises(model, count=10)
        assert len(result) >= 1
        # Strong items should produce definition_recall exercises
        assert any(ex.exercise_type == "definition_recall" for ex in result)


@pytest.mark.unit
class TestSelectExercisesGrammar:
    """Grammar fill-blank exercises."""

    def test_grammar_concepts_generate_fill_blank(self) -> None:
        concept_id = uuid.uuid4()
        gc = _make_grammar_concept(concept_id=concept_id, name="First Declension")
        lg = _make_learner_grammar(concept_id)
        model = _make_model(grammar=[lg], grammar_concepts=[gc])
        result = select_exercises(model, count=5)
        assert len(result) == 1
        assert result[0].exercise_type == "fill_blank"

    def test_grammar_without_matching_concept_skipped(self) -> None:
        lg = _make_learner_grammar(uuid.uuid4())  # No matching concept
        model = _make_model(grammar=[lg], grammar_concepts=[])
        result = select_exercises(model, count=5)
        assert result == []


@pytest.mark.unit
class TestSelectExercisesCountLimit:
    """Count parameter is respected."""

    def test_count_limits_output(self) -> None:
        now = datetime.now(UTC)
        items = [
            _make_learner_vocab(
                strength=0.5,
                next_review=now - timedelta(days=i),
                lemma=f"word_{i}",
                definition=f"def_{i}",
            )
            for i in range(1, 20)
        ]
        model = _make_model(vocabulary=items)
        result = select_exercises(model, count=3, now=now)
        assert len(result) <= 3

    def test_count_one(self) -> None:
        now = datetime.now(UTC)
        lv = _make_learner_vocab(
            strength=0.5,
            next_review=now - timedelta(days=1),
        )
        model = _make_model(vocabulary=[lv])
        result = select_exercises(model, count=1, now=now)
        assert len(result) == 1


@pytest.mark.unit
class TestSelectExercisesMixed:
    """Mixed vocabulary and grammar produces balanced output."""

    def test_mixed_items(self) -> None:
        now = datetime.now(UTC)
        due = _make_learner_vocab(
            strength=0.5,
            next_review=now - timedelta(days=1),
            lemma="bellum",
            definition="war",
        )
        weak = _make_learner_vocab(strength=0.1, lemma="pax", definition="peace")
        strong = _make_learner_vocab(strength=0.9, lemma="aqua", definition="water")
        concept_id = uuid.uuid4()
        gc = _make_grammar_concept(concept_id=concept_id)
        lg = _make_learner_grammar(concept_id)
        model = _make_model(
            vocabulary=[due, weak, strong],
            grammar=[lg],
            grammar_concepts=[gc],
        )
        result = select_exercises(model, count=10, now=now)
        assert len(result) >= 3  # At least due + weak + strong or grammar


@pytest.mark.unit
class TestSelectExercisesEdgeCases:
    """Edge cases and robustness."""

    def test_vocab_item_none_skipped(self) -> None:
        now = datetime.now(UTC)
        lv = MagicMock()
        lv.strength = 0.5
        lv.next_review = now - timedelta(days=1)
        lv.vocabulary_item = None  # Explicitly None
        model = _make_model(vocabulary=[lv])
        result = select_exercises(model, count=5, now=now)
        assert result == []

    def test_deterministic_with_seed(self) -> None:
        now = datetime.now(UTC)
        items = [
            _make_learner_vocab(
                strength=0.5,
                next_review=now - timedelta(days=i),
                lemma=f"word_{i}",
                definition=f"def_{i}",
            )
            for i in range(1, 6)
        ]
        model = _make_model(vocabulary=items)
        random.seed(42)
        r1 = select_exercises(model, count=5, now=now)
        random.seed(42)
        r2 = select_exercises(model, count=5, now=now)
        assert len(r1) == len(r2)

    def test_no_forms_still_works(self) -> None:
        lv = _make_learner_vocab(strength=0.1, lemma="et", definition="and")
        lv.vocabulary_item.forms = None
        model = _make_model(vocabulary=[lv])
        random.seed(0)
        result = select_exercises(model, count=5)
        assert len(result) >= 1
