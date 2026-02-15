import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from instructor.models import (
    GrammarConcept,
    Learner,
    LearnerLanguageState,
    LearnerVocabulary,
    VocabularyItem,
)
from instructor.models.enums import (
    GrammarCategory,
    Language,
    PartOfSpeech,
)


@pytest.mark.integration
async def test_all_tables_created(db_session: AsyncSession) -> None:
    """Verify all expected tables exist."""
    result = await db_session.execute(
        text(
            "SELECT tablename FROM pg_tables"
            " WHERE schemaname = 'public' ORDER BY tablename"
        )
    )
    tables = {row[0] for row in result.fetchall()}
    expected = {
        "learners",
        "learner_language_states",
        "vocabulary_items",
        "learner_vocabulary",
        "grammar_concepts",
        "learner_grammar",
        "text_entries",
        "sessions",
        "session_activities",
        "exercises",
    }
    assert expected.issubset(tables), f"Missing tables: {expected - tables}"


@pytest.mark.integration
async def test_learner_language_state_unique_constraint(
    db_session_committed: AsyncSession,
) -> None:
    """Duplicate learner+language should be rejected."""
    learner = Learner(name="Test Learner")
    db_session_committed.add(learner)
    await db_session_committed.flush()

    state1 = LearnerLanguageState(learner_id=learner.id, language=Language.LATIN)
    db_session_committed.add(state1)
    await db_session_committed.commit()

    state2 = LearnerLanguageState(learner_id=learner.id, language=Language.LATIN)
    db_session_committed.add(state2)
    with pytest.raises(IntegrityError):
        await db_session_committed.commit()


@pytest.mark.integration
async def test_learner_cascade_delete(
    db_session_committed: AsyncSession,
) -> None:
    """Deleting a learner should cascade to language states and vocabulary."""
    learner = Learner(name="Cascade Test")
    db_session_committed.add(learner)
    await db_session_committed.flush()

    state = LearnerLanguageState(learner_id=learner.id, language=Language.GREEK)
    db_session_committed.add(state)
    await db_session_committed.commit()

    # Delete learner
    await db_session_committed.delete(learner)
    await db_session_committed.commit()

    # Verify cascade
    result = await db_session_committed.execute(
        text("SELECT count(*) FROM learner_language_states")
    )
    assert result.scalar() == 0


@pytest.mark.integration
async def test_vocabulary_unique_constraint(
    db_session_committed: AsyncSession,
) -> None:
    """Duplicate language+lemma+pos should be rejected."""
    v1 = VocabularyItem(
        language=Language.LATIN,
        lemma="sum",
        part_of_speech=PartOfSpeech.VERB,
        definition="to be",
        difficulty_level=1,
    )
    db_session_committed.add(v1)
    await db_session_committed.commit()

    v2 = VocabularyItem(
        language=Language.LATIN,
        lemma="sum",
        part_of_speech=PartOfSpeech.VERB,
        definition="to be (duplicate)",
        difficulty_level=1,
    )
    db_session_committed.add(v2)
    with pytest.raises(IntegrityError):
        await db_session_committed.commit()


@pytest.mark.integration
async def test_learner_vocabulary_unique_constraint(
    db_session_committed: AsyncSession,
) -> None:
    """Duplicate learner+vocabulary_item should be rejected."""
    learner = Learner(name="Vocab Test")
    vocab = VocabularyItem(
        language=Language.LATIN,
        lemma="et",
        part_of_speech=PartOfSpeech.CONJUNCTION,
        definition="and",
        difficulty_level=1,
    )
    db_session_committed.add_all([learner, vocab])
    await db_session_committed.flush()

    lv1 = LearnerVocabulary(
        learner_id=learner.id, vocabulary_item_id=vocab.id
    )
    db_session_committed.add(lv1)
    await db_session_committed.commit()

    lv2 = LearnerVocabulary(
        learner_id=learner.id, vocabulary_item_id=vocab.id
    )
    db_session_committed.add(lv2)
    with pytest.raises(IntegrityError):
        await db_session_committed.commit()


@pytest.mark.integration
async def test_grammar_unique_constraint(
    db_session_committed: AsyncSession,
) -> None:
    """Duplicate language+name should be rejected."""
    g1 = GrammarConcept(
        language=Language.LATIN,
        category=GrammarCategory.MORPHOLOGY,
        subcategory="noun_declension",
        name="First Declension",
        description="Nouns with -a stems",
        difficulty_level=1,
    )
    db_session_committed.add(g1)
    await db_session_committed.commit()

    g2 = GrammarConcept(
        language=Language.LATIN,
        category=GrammarCategory.MORPHOLOGY,
        subcategory="noun_declension",
        name="First Declension",
        description="Duplicate",
        difficulty_level=1,
    )
    db_session_committed.add(g2)
    with pytest.raises(IntegrityError):
        await db_session_committed.commit()


@pytest.mark.integration
async def test_indexes_exist(db_session: AsyncSession) -> None:
    """Verify key indexes are created."""
    result = await db_session.execute(
        text(
            "SELECT indexname FROM pg_indexes"
            " WHERE schemaname = 'public' ORDER BY indexname"
        )
    )
    indexes = {row[0] for row in result.fetchall()}

    expected_indexes = {
        "ix_learner_vocab_next_review",
        "ix_learner_vocab_strength",
        "ix_learner_grammar_mastery",
        "ix_sessions_learner_lang",
    }
    assert expected_indexes.issubset(indexes), (
        f"Missing indexes: {expected_indexes - indexes}"
    )
