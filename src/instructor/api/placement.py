"""Placement assessment API routes."""

from __future__ import annotations

from fastapi import APIRouter

from instructor.api.schemas import (
    PlacementResultResponse,
    PlacementSubmitRequest,
)
from instructor.evaluator.placement import (
    PlacementResponse,
    score_placement,
)

router = APIRouter(prefix="/api/placement", tags=["placement"])


@router.post("", response_model=PlacementResultResponse)
async def submit_placement(
    request: PlacementSubmitRequest,
) -> PlacementResultResponse:
    """Score placement test responses and return starting level."""
    responses = [
        PlacementResponse(
            probe_type=r.probe_type,
            difficulty=r.difficulty,
            correct=r.correct,
            item_id=r.item_id,
        )
        for r in request.responses
    ]
    result = score_placement(responses)
    return PlacementResultResponse(
        total_score=result.total_score,
        vocabulary_score=result.vocabulary_score,
        grammar_score=result.grammar_score,
        reading_score=result.reading_score,
        starting_unit=result.starting_unit,
    )
