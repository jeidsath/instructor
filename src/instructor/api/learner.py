"""Learner API routes."""

import uuid

from fastapi import APIRouter, HTTPException

from instructor.api.schemas import (
    CreateLearnerRequest,
    LearnerResponse,
    LearnerStateResponse,
)
from instructor.models.enums import Language

router = APIRouter(prefix="/api/learners", tags=["learners"])


@router.post("", response_model=LearnerResponse, status_code=201)
async def create_learner(request: CreateLearnerRequest) -> LearnerResponse:
    """Create a new learner."""
    # DB persistence will be added when wiring up the database session.
    return LearnerResponse(id=uuid.uuid4(), name=request.name)


@router.get("/{learner_id}", response_model=LearnerResponse)
async def get_learner(learner_id: uuid.UUID) -> LearnerResponse:
    """Get a learner by ID."""
    # Placeholder — DB lookup will be added.
    msg = f"Learner {learner_id} not found"
    raise HTTPException(status_code=404, detail=msg)


@router.get(
    "/{learner_id}/state/{language}",
    response_model=LearnerStateResponse,
)
async def get_learner_state(
    learner_id: uuid.UUID, language: Language
) -> LearnerStateResponse:
    """Get a learner's state for a specific language."""
    msg = f"State not found for learner {learner_id}, language {language}"
    raise HTTPException(status_code=404, detail=msg)
