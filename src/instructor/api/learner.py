"""Learner API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from instructor.api.schemas import (
    CreateLearnerRequest,
    LearnerResponse,
    LearnerStateResponse,
)
from instructor.db import get_db
from instructor.models.enums import Language
from instructor.models.learner import Learner, LearnerLanguageState

router = APIRouter(prefix="/api/learners", tags=["learners"])


@router.post("", response_model=LearnerResponse, status_code=201)
async def create_learner(
    request: CreateLearnerRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearnerResponse:
    """Create a new learner."""
    learner = Learner(name=request.name)
    db.add(learner)
    await db.commit()
    await db.refresh(learner)
    return LearnerResponse.model_validate(learner)


@router.get("/{learner_id}", response_model=LearnerResponse)
async def get_learner(
    learner_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearnerResponse:
    """Get a learner by ID."""
    learner = await db.get(Learner, learner_id)
    if learner is None:
        raise HTTPException(status_code=404, detail=f"Learner {learner_id} not found")
    return LearnerResponse.model_validate(learner)


@router.get(
    "/{learner_id}/state/{language}",
    response_model=LearnerStateResponse,
)
async def get_learner_state(
    learner_id: uuid.UUID,
    language: Language,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LearnerStateResponse:
    """Get a learner's state for a specific language."""
    learner = await db.get(Learner, learner_id)
    if learner is None:
        raise HTTPException(status_code=404, detail=f"Learner {learner_id} not found")

    result = await db.execute(
        select(LearnerLanguageState).where(
            LearnerLanguageState.learner_id == learner_id,
            LearnerLanguageState.language == language,
        )
    )
    state = result.scalar_one_or_none()
    if state is None:
        msg = f"No state for learner {learner_id}, language {language.value}"
        raise HTTPException(status_code=404, detail=msg)
    return LearnerStateResponse.model_validate(state)
