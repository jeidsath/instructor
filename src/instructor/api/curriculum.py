"""Curriculum browsing API routes."""

from __future__ import annotations

from fastapi import APIRouter

from instructor.api.schemas import (
    GrammarConceptResponse,
    VocabularySetResponse,
)
from instructor.config import settings
from instructor.curriculum.registry import CurriculumRegistry
from instructor.models.enums import Language

router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])


def _get_registry() -> CurriculumRegistry:
    return CurriculumRegistry(settings.curriculum_path)


@router.get(
    "/{language}/vocabulary",
    response_model=list[VocabularySetResponse],
)
async def list_vocabulary_sets(
    language: Language,
) -> list[VocabularySetResponse]:
    """List available vocabulary sets for a language."""
    registry = _get_registry()
    vocab_sets = registry.get_vocabulary_sets(language.value)
    return [
        VocabularySetResponse(
            set_name=vs.set,
            language=Language(vs.language),
            item_count=len(vs.items),
        )
        for vs in vocab_sets
    ]


@router.get(
    "/{language}/grammar",
    response_model=list[GrammarConceptResponse],
)
async def list_grammar_concepts(
    language: Language,
) -> list[GrammarConceptResponse]:
    """List grammar concepts for a language."""
    registry = _get_registry()
    concepts = registry.get_grammar_concepts(language.value)
    return [
        GrammarConceptResponse(
            name=gc.name,
            category=gc.subcategory,
            subcategory=gc.subcategory,
            difficulty_level=gc.difficulty,
            prerequisite_names=gc.prerequisites or [],
        )
        for gc in concepts
    ]
