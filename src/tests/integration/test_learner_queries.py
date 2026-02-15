import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from instructor.learner.queries import load_learner_model
from instructor.models.enums import Language, MasteryLevel
from instructor.models.grammar import GrammarConcept, LearnerGrammar
from instructor.models.learner import Learner, LearnerLanguageState
from instructor.models.vocabulary import LearnerVocabulary, VocabularyItem

NOW = datetime(2026, 3, 1, 12, 0, 0, tzinfo=UTC)


@pytest.mark.integration
class TestLoadLearnerModel:
    """load_learner_model assembles a correct aggregate from the database."""

    @pytest.fixture
    async def seeded_learner(
        self, db_session: AsyncSession
    ) -> tuple[uuid.UUID, Language]:
        """Create a learner with vocabulary and grammar in the DB."""
        learner = Learner(name="Integration Test Learner")
        db_session.add(learner)
        await db_session.flush()

        lang = Language.LATIN
        state = LearnerLanguageState(
            learner_id=learner.id,
            language=lang,
            reading_level=3.0,
            writing_level=2.0,
            listening_level=1.0,
            speaking_level=4.0,
            last_session_at=NOW,
        )
        db_session.add(state)

        vocab_item = VocabularyItem(
            language=lang,
            lemma="amō",
            part_of_speech="verb",
            definition="to love",
            difficulty_level=1,
        )
        db_session.add(vocab_item)
        await db_session.flush()

        learner_vocab = LearnerVocabulary(
            learner_id=learner.id,
            vocabulary_item_id=vocab_item.id,
            strength=0.8,
            ease_factor=2.5,
            interval_days=10.0,
            repetition_count=3,
            last_reviewed=NOW - timedelta(days=5),
            next_review=NOW - timedelta(days=1),
        )
        db_session.add(learner_vocab)

        concept = GrammarConcept(
            language=lang,
            category="morphology",
            subcategory="noun_declension",
            name="Integration First Declension",
            description="Test concept",
            difficulty_level=1,
        )
        db_session.add(concept)
        await db_session.flush()

        learner_grammar = LearnerGrammar(
            learner_id=learner.id,
            grammar_concept_id=concept.id,
            mastery_level=MasteryLevel.FAMILIAR,
            times_practiced=10,
            recent_error_rate=0.1,
        )
        db_session.add(learner_grammar)
        await db_session.flush()

        return learner.id, lang

    async def test_loads_complete_model(
        self,
        db_session: AsyncSession,
        seeded_learner: tuple[uuid.UUID, Language],
    ) -> None:
        learner_id, lang = seeded_learner
        model = await load_learner_model(db_session, learner_id, lang)

        assert model.learner.name == "Integration Test Learner"
        assert model.language == lang
        assert model.state.reading_level == 3.0
        assert len(model.vocabulary) == 1
        assert model.vocabulary[0].strength == 0.8
        assert len(model.grammar) == 1
        assert model.grammar[0].mastery_level == MasteryLevel.FAMILIAR
        assert len(model.grammar_concepts) >= 1

    async def test_due_vocabulary_from_loaded_model(
        self,
        db_session: AsyncSession,
        seeded_learner: tuple[uuid.UUID, Language],
    ) -> None:
        learner_id, lang = seeded_learner
        model = await load_learner_model(db_session, learner_id, lang)
        due = model.vocabulary_due_for_review(now=NOW)
        assert len(due) == 1

    async def test_missing_learner_raises(self, db_session: AsyncSession) -> None:
        with pytest.raises(ValueError, match="not found"):
            await load_learner_model(db_session, uuid.uuid4(), Language.LATIN)

    async def test_missing_language_state_raises(
        self,
        db_session: AsyncSession,
        seeded_learner: tuple[uuid.UUID, Language],
    ) -> None:
        learner_id, _ = seeded_learner
        with pytest.raises(ValueError, match="No language state"):
            await load_learner_model(db_session, learner_id, Language.GREEK)

    async def test_empty_learner(self, db_session: AsyncSession) -> None:
        """A learner with no vocabulary or grammar loads cleanly."""
        learner = Learner(name="Empty Learner")
        db_session.add(learner)
        await db_session.flush()

        state = LearnerLanguageState(
            learner_id=learner.id,
            language=Language.LATIN,
        )
        db_session.add(state)
        await db_session.flush()

        model = await load_learner_model(db_session, learner.id, Language.LATIN)
        assert model.vocabulary == []
        assert model.grammar == []
