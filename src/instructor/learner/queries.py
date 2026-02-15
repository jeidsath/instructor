"""Database queries for loading :class:`LearnerModel` aggregates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from instructor.learner.model import LearnerModel
from instructor.models.grammar import GrammarConcept, LearnerGrammar
from instructor.models.learner import Learner, LearnerLanguageState
from instructor.models.vocabulary import LearnerVocabulary

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from instructor.models.enums import Language


async def load_learner_model(
    db: AsyncSession,
    learner_id: object,
    language: Language,
) -> LearnerModel:
    """Assemble a :class:`LearnerModel` from the database.

    Loads the learner, their language state, all vocabulary items,
    grammar mastery records, and the full grammar concept catalogue
    for the given language.

    Raises:
        ValueError: If the learner or language state is not found.
    """
    learner = await db.get(Learner, learner_id)
    if learner is None:
        msg = f"Learner {learner_id} not found"
        raise ValueError(msg)

    state_result = await db.execute(
        select(LearnerLanguageState).where(
            LearnerLanguageState.learner_id == learner_id,
            LearnerLanguageState.language == language,
        )
    )
    state = state_result.scalar_one_or_none()
    if state is None:
        msg = f"No language state for learner {learner_id}, language {language}"
        raise ValueError(msg)

    vocab_result = await db.execute(
        select(LearnerVocabulary).where(
            LearnerVocabulary.learner_id == learner_id,
        )
    )
    vocabulary = list(vocab_result.scalars().all())

    grammar_result = await db.execute(
        select(LearnerGrammar).where(
            LearnerGrammar.learner_id == learner_id,
        )
    )
    grammar = list(grammar_result.scalars().all())

    concepts_result = await db.execute(
        select(GrammarConcept).where(
            GrammarConcept.language == language,
        )
    )
    grammar_concepts = list(concepts_result.scalars().all())

    return LearnerModel(
        learner=learner,
        language=language,
        state=state,
        vocabulary=vocabulary,
        grammar=grammar,
        grammar_concepts=grammar_concepts,
    )
