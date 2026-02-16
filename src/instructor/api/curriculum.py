"""Curriculum browsing API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from instructor.api.schemas import (
    GrammarConceptResponse,
    VocabularySetResponse,
)
from instructor.curriculum.registry import CurriculumRegistry
from instructor.models.enums import Language

router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])


def get_registry(request: Request) -> CurriculumRegistry:
    """Return the application-wide CurriculumRegistry singleton."""
    return request.app.state.registry  # type: ignore[no-any-return]


@router.get(
    "/{language}/vocabulary",
    response_model=list[VocabularySetResponse],
)
async def list_vocabulary_sets(
    language: Language,
    registry: Annotated[CurriculumRegistry, Depends(get_registry)],
) -> list[VocabularySetResponse]:
    """List available vocabulary sets for a language."""
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
    registry: Annotated[CurriculumRegistry, Depends(get_registry)],
) -> list[GrammarConceptResponse]:
    """List grammar concepts for a language."""
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
