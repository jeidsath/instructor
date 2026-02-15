import uuid
from datetime import UTC, datetime, timedelta

import pytest

from instructor.learner.model import REVIEW_THRESHOLD, LearnerModel
from instructor.models.enums import Language, MasteryLevel, SessionType
from instructor.models.grammar import GrammarConcept, LearnerGrammar
from instructor.models.learner import Learner, LearnerLanguageState
from instructor.models.vocabulary import LearnerVocabulary

NOW = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
LEARNER_ID = uuid.uuid4()


def _learner() -> Learner:
    return Learner(id=LEARNER_ID, name="Test Learner")


def _state(**overrides: object) -> LearnerLanguageState:
    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "learner_id": LEARNER_ID,
        "language": Language.LATIN,
        "reading_level": 3.0,
        "writing_level": 2.0,
        "listening_level": 1.0,
        "speaking_level": 4.0,
        "active_vocabulary_size": 0,
        "grammar_concepts_mastered": 0,
        "current_unit": None,
        "last_session_at": NOW - timedelta(days=1),
        "total_study_time_minutes": 60,
    }
    defaults.update(overrides)
    return LearnerLanguageState(**defaults)


def _vocab(
    *,
    strength: float = 0.5,
    next_review: datetime | None = None,
) -> LearnerVocabulary:
    return LearnerVocabulary(
        id=uuid.uuid4(),
        learner_id=LEARNER_ID,
        vocabulary_item_id=uuid.uuid4(),
        strength=strength,
        ease_factor=2.5,
        interval_days=5.0,
        repetition_count=1,
        last_reviewed=NOW - timedelta(days=3),
        next_review=next_review,
        times_correct=3,
        times_incorrect=0,
    )


def _grammar(
    concept_id: uuid.UUID,
    mastery: MasteryLevel = MasteryLevel.UNKNOWN,
) -> LearnerGrammar:
    return LearnerGrammar(
        id=uuid.uuid4(),
        learner_id=LEARNER_ID,
        grammar_concept_id=concept_id,
        mastery_level=mastery,
        last_practiced=NOW - timedelta(days=1),
        times_practiced=5,
        recent_error_rate=0.1,
    )


def _concept(
    name: str,
    prereqs: list[str] | None = None,
) -> GrammarConcept:
    return GrammarConcept(
        id=uuid.uuid4(),
        language=Language.LATIN,
        category="morphology",
        subcategory="noun_declension",
        name=name,
        description="test concept",
        difficulty_level=1,
        prerequisite_ids=prereqs,
    )


def _model(
    *,
    vocabulary: list[LearnerVocabulary] | None = None,
    grammar: list[LearnerGrammar] | None = None,
    grammar_concepts: list[GrammarConcept] | None = None,
    state: LearnerLanguageState | None = None,
) -> LearnerModel:
    return LearnerModel(
        learner=_learner(),
        language=Language.LATIN,
        state=state or _state(),
        vocabulary=vocabulary or [],
        grammar=grammar or [],
        grammar_concepts=grammar_concepts or [],
    )


@pytest.mark.unit
class TestVocabularyDueForReview:
    """vocabulary_due_for_review filters and orders correctly."""

    def test_returns_overdue_items(self) -> None:
        v1 = _vocab(next_review=NOW - timedelta(days=2))
        v2 = _vocab(next_review=NOW - timedelta(days=1))
        v3 = _vocab(next_review=NOW + timedelta(days=1))
        m = _model(vocabulary=[v1, v2, v3])
        due = m.vocabulary_due_for_review(now=NOW)
        assert len(due) == 2
        assert due[0] is v1  # most overdue first
        assert due[1] is v2

    def test_includes_items_due_exactly_now(self) -> None:
        v = _vocab(next_review=NOW)
        m = _model(vocabulary=[v])
        assert len(m.vocabulary_due_for_review(now=NOW)) == 1

    def test_excludes_items_with_no_review_date(self) -> None:
        v = _vocab(next_review=None)
        m = _model(vocabulary=[v])
        assert len(m.vocabulary_due_for_review(now=NOW)) == 0

    def test_empty_vocabulary(self) -> None:
        m = _model()
        assert m.vocabulary_due_for_review(now=NOW) == []


@pytest.mark.unit
class TestWeakAndStrongVocabulary:
    """weak_vocabulary and strong_vocabulary filter at thresholds."""

    def test_weak_below_threshold(self) -> None:
        v1 = _vocab(strength=0.1)
        v2 = _vocab(strength=0.5)
        m = _model(vocabulary=[v1, v2])
        assert m.weak_vocabulary(threshold=0.3) == [v1]

    def test_weak_at_threshold_excluded(self) -> None:
        v = _vocab(strength=0.3)
        m = _model(vocabulary=[v])
        assert m.weak_vocabulary(threshold=0.3) == []

    def test_strong_above_threshold(self) -> None:
        v1 = _vocab(strength=0.8)
        v2 = _vocab(strength=0.5)
        m = _model(vocabulary=[v1, v2])
        assert m.strong_vocabulary(threshold=0.7) == [v1]

    def test_strong_at_threshold_excluded(self) -> None:
        v = _vocab(strength=0.7)
        m = _model(vocabulary=[v])
        assert m.strong_vocabulary(threshold=0.7) == []


@pytest.mark.unit
class TestGrammarAtLevel:
    """grammar_at_level returns correct subset."""

    def test_filters_by_level(self) -> None:
        c1 = _concept("A")
        c2 = _concept("B")
        g1 = _grammar(c1.id, MasteryLevel.FAMILIAR)
        g2 = _grammar(c2.id, MasteryLevel.PROFICIENT)
        m = _model(grammar=[g1, g2])
        result = m.grammar_at_level(MasteryLevel.FAMILIAR)
        assert len(result) == 1
        assert result[0] is g1

    def test_empty_when_no_match(self) -> None:
        c = _concept("A")
        g = _grammar(c.id, MasteryLevel.PRACTICING)
        m = _model(grammar=[g])
        assert m.grammar_at_level(MasteryLevel.MASTERED) == []


@pytest.mark.unit
class TestNextGrammarConcepts:
    """next_grammar_concepts respects prerequisite graph."""

    def test_returns_concepts_with_no_prereqs(self) -> None:
        c = _concept("First Declension", prereqs=[])
        m = _model(grammar_concepts=[c])
        assert m.next_grammar_concepts() == [c]

    def test_excludes_already_introduced(self) -> None:
        c = _concept("First Declension")
        g = _grammar(c.id, MasteryLevel.INTRODUCED)
        m = _model(grammar=[g], grammar_concepts=[c])
        assert m.next_grammar_concepts() == []

    def test_prereqs_not_met(self) -> None:
        c1 = _concept("First Declension")
        c2 = _concept("Third Declension", prereqs=["First Declension"])
        g1 = _grammar(c1.id, MasteryLevel.FAMILIAR)  # only FAMILIAR, not PROFICIENT
        m = _model(grammar=[g1], grammar_concepts=[c1, c2])
        # c1 is already introduced (excluded), c2's prereq is not PROFICIENT
        assert m.next_grammar_concepts() == []

    def test_prereqs_met(self) -> None:
        c1 = _concept("First Declension")
        c2 = _concept("Third Declension", prereqs=["First Declension"])
        g1 = _grammar(c1.id, MasteryLevel.PROFICIENT)
        m = _model(grammar=[g1], grammar_concepts=[c1, c2])
        result = m.next_grammar_concepts()
        assert len(result) == 1
        assert result[0].name == "Third Declension"

    def test_multiple_prereqs_all_must_be_met(self) -> None:
        c1 = _concept("A")
        c2 = _concept("B")
        c3 = _concept("C", prereqs=["A", "B"])
        g1 = _grammar(c1.id, MasteryLevel.PROFICIENT)
        g2 = _grammar(c2.id, MasteryLevel.FAMILIAR)  # not proficient
        m = _model(grammar=[g1, g2], grammar_concepts=[c1, c2, c3])
        assert m.next_grammar_concepts() == []

    def test_no_concepts_available(self) -> None:
        m = _model()
        assert m.next_grammar_concepts() == []


@pytest.mark.unit
class TestWeakestCapacity:
    """weakest_capacity returns the lowest-scoring capacity."""

    def test_returns_lowest(self) -> None:
        s = _state(
            reading_level=3.0,
            writing_level=2.0,
            listening_level=1.0,
            speaking_level=4.0,
        )
        m = _model(state=s)
        assert m.weakest_capacity() == "listening"

    def test_tie_returns_first_in_order(self) -> None:
        s = _state(
            reading_level=1.0,
            writing_level=1.0,
            listening_level=2.0,
            speaking_level=3.0,
        )
        m = _model(state=s)
        assert m.weakest_capacity() == "reading"

    def test_all_equal(self) -> None:
        s = _state(
            reading_level=5.0,
            writing_level=5.0,
            listening_level=5.0,
            speaking_level=5.0,
        )
        m = _model(state=s)
        assert m.weakest_capacity() == "reading"


@pytest.mark.unit
class TestRecommendedSessionType:
    """recommended_session_type returns appropriate session type."""

    def test_placement_for_new_learner(self) -> None:
        s = _state(last_session_at=None)
        m = _model(state=s)
        assert m.recommended_session_type(now=NOW) == SessionType.PLACEMENT

    def test_practice_when_many_due(self) -> None:
        vocab = [
            _vocab(next_review=NOW - timedelta(days=i)) for i in range(REVIEW_THRESHOLD)
        ]
        m = _model(vocabulary=vocab)
        assert m.recommended_session_type(now=NOW) == SessionType.PRACTICE

    def test_lesson_when_concepts_available(self) -> None:
        c = _concept("First Declension", prereqs=[])
        m = _model(grammar_concepts=[c])
        assert m.recommended_session_type(now=NOW) == SessionType.LESSON

    def test_practice_as_fallback(self) -> None:
        m = _model()
        assert m.recommended_session_type(now=NOW) == SessionType.PRACTICE

    def test_practice_takes_priority_over_lesson(self) -> None:
        vocab = [
            _vocab(next_review=NOW - timedelta(days=i)) for i in range(REVIEW_THRESHOLD)
        ]
        c = _concept("First Declension", prereqs=[])
        m = _model(vocabulary=vocab, grammar_concepts=[c])
        assert m.recommended_session_type(now=NOW) == SessionType.PRACTICE
