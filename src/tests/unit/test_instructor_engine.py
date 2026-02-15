import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest

from instructor.ai.client import AIClient
from instructor.instructor_engine.engine import (
    build_grammar_lesson,
    build_vocabulary_lesson,
    select_next_topic,
)
from instructor.instructor_engine.explainer import explain_concept, explain_error
from instructor.instructor_engine.generator import (
    generate_grammar_lesson,
    generate_vocabulary_lesson,
)
from instructor.learner.model import LearnerModel
from instructor.models.enums import Language, MasteryLevel
from instructor.models.grammar import GrammarConcept, LearnerGrammar
from instructor.models.learner import Learner, LearnerLanguageState
from instructor.models.vocabulary import LearnerVocabulary

NOW = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)
LEARNER_ID = uuid.uuid4()


def _concept(name: str, prereqs: list[str] | None = None) -> GrammarConcept:
    return GrammarConcept(
        id=uuid.uuid4(),
        language=Language.LATIN,
        category="morphology",
        subcategory="noun_declension",
        name=name,
        description=f"Test concept: {name}",
        difficulty_level=1,
        prerequisite_ids=prereqs,
    )


def _model(
    *,
    grammar_concepts: list[GrammarConcept] | None = None,
    grammar: list[LearnerGrammar] | None = None,
    vocabulary: list[LearnerVocabulary] | None = None,
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
            last_session_at=NOW - timedelta(days=1),
        ),
        grammar_concepts=grammar_concepts or [],
        grammar=grammar or [],
        vocabulary=vocabulary or [],
    )


def _mock_client(data: dict[str, Any]) -> AIClient:
    client = MagicMock(spec=AIClient)
    client.complete_json.return_value = data
    return client


# ------------------------------------------------------------------
# Topic selection
# ------------------------------------------------------------------


@pytest.mark.unit
class TestSelectNextTopic:
    """select_next_topic picks from available concepts."""

    def test_grammar_concept_available(self) -> None:
        c = _concept("First Declension", prereqs=[])
        model = _model(grammar_concepts=[c])
        topic = select_next_topic(model)
        assert topic is not None
        assert topic.topic_type == "grammar"
        assert topic.name == "First Declension"

    def test_no_concepts_returns_none(self) -> None:
        model = _model()
        assert select_next_topic(model) is None

    def test_all_concepts_introduced_returns_none(self) -> None:
        c = _concept("A")
        g = LearnerGrammar(
            id=uuid.uuid4(),
            learner_id=LEARNER_ID,
            grammar_concept_id=c.id,
            mastery_level=MasteryLevel.INTRODUCED,
            times_practiced=5,
            recent_error_rate=0.1,
        )
        model = _model(grammar_concepts=[c], grammar=[g])
        assert select_next_topic(model) is None

    def test_concept_with_difficulty(self) -> None:
        c = _concept("First Declension")
        model = _model(grammar_concepts=[c])
        topic = select_next_topic(model)
        assert topic is not None
        assert topic.difficulty == 1


# ------------------------------------------------------------------
# Template-based lesson building
# ------------------------------------------------------------------


@pytest.mark.unit
class TestBuildGrammarLesson:
    """build_grammar_lesson creates structural template."""

    def test_has_title(self) -> None:
        c = _concept("First Declension")
        model = _model()
        lesson = build_grammar_lesson(c, model)
        assert lesson.title == "First Declension"

    def test_has_explanation(self) -> None:
        c = _concept("First Declension")
        model = _model()
        lesson = build_grammar_lesson(c, model)
        assert "First Declension" in lesson.explanation

    def test_mentions_weakest_capacity(self) -> None:
        model = _model()  # listening is weakest
        c = _concept("First Declension")
        lesson = build_grammar_lesson(c, model)
        assert "listening" in lesson.summary

    def test_has_practice_prompts(self) -> None:
        c = _concept("First Declension")
        model = _model()
        lesson = build_grammar_lesson(c, model)
        assert len(lesson.practice_prompts) > 0


@pytest.mark.unit
class TestBuildVocabularyLesson:
    """build_vocabulary_lesson creates review lesson."""

    def test_has_title(self) -> None:
        model = _model()
        lesson = build_vocabulary_lesson(["amō", "rosa"], model)
        assert lesson.title == "Vocabulary Review"

    def test_lists_words(self) -> None:
        model = _model()
        lesson = build_vocabulary_lesson(["amō", "rosa"], model)
        assert "amō" in lesson.explanation
        assert "rosa" in lesson.explanation

    def test_practice_prompts_per_word(self) -> None:
        model = _model()
        lesson = build_vocabulary_lesson(["amō", "rosa", "via"], model)
        assert len(lesson.practice_prompts) == 3


# ------------------------------------------------------------------
# AI-powered generation
# ------------------------------------------------------------------


@pytest.mark.unit
class TestGenerateGrammarLesson:
    """generate_grammar_lesson calls AI and parses response."""

    def test_returns_lesson_content(self) -> None:
        client = _mock_client(
            {
                "explanation": "The first declension...",
                "examples": ["Rosa est pulchra."],
                "paradigm_table": {"nom_sg": "rosa", "gen_sg": "rosae"},
                "summary": "Key: -a stem nouns.",
            }
        )
        c = _concept("First Declension")
        lesson = generate_grammar_lesson(client, c, language="Latin", level=3.0)
        assert lesson.title == "First Declension"
        assert "first declension" in lesson.explanation.lower()
        assert len(lesson.examples) == 1
        assert lesson.paradigm_table is not None

    def test_null_paradigm_table(self) -> None:
        client = _mock_client(
            {
                "explanation": "Test",
                "examples": [],
                "paradigm_table": None,
                "summary": "Test",
            }
        )
        c = _concept("Syntax Rule")
        lesson = generate_grammar_lesson(client, c, language="Latin", level=3.0)
        assert lesson.paradigm_table is None


@pytest.mark.unit
class TestGenerateVocabularyLesson:
    """generate_vocabulary_lesson calls AI and parses response."""

    def test_returns_lesson_content(self) -> None:
        client = _mock_client(
            {
                "explanation": "These are common verbs.",
                "examples": ["amō — I love"],
                "summary": "Practice these verbs daily.",
            }
        )
        lesson = generate_vocabulary_lesson(
            client, ["amō", "timeō"], language="Latin", level=2.0
        )
        assert lesson.title == "Vocabulary Lesson"
        assert len(lesson.examples) == 1


# ------------------------------------------------------------------
# Explainer
# ------------------------------------------------------------------


@pytest.mark.unit
class TestExplainError:
    """explain_error generates pedagogical feedback."""

    def test_returns_explanation_and_tip(self) -> None:
        client = _mock_client(
            {
                "explanation": "The accusative case is needed here.",
                "tip": "Remember: direct objects take accusative.",
            }
        )
        explanation, tip = explain_error(
            client,
            language="Latin",
            exercise_type="fill_blank",
            prompt="Puella ___ videt.",
            response="rosa",
            expected="rosam",
            score=0.0,
        )
        assert "accusative" in explanation
        assert len(tip) > 0

    def test_missing_fields_default_empty(self) -> None:
        client = _mock_client({})
        explanation, tip = explain_error(
            client,
            language="Latin",
            exercise_type="test",
            prompt="p",
            response="r",
            expected="e",
            score=0.0,
        )
        assert explanation == ""
        assert tip == ""


@pytest.mark.unit
class TestExplainConcept:
    """explain_concept generates on-demand explanations."""

    def test_returns_explanation_and_example(self) -> None:
        client = _mock_client(
            {
                "explanation": "The ablative case shows means.",
                "example": "Gladiō pugnat — He fights with a sword.",
            }
        )
        explanation, example = explain_concept(
            client,
            language="Latin",
            concept_name="Ablative of Means",
            level=3.0,
        )
        assert "ablative" in explanation.lower()
        assert "Gladiō" in example
