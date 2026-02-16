"""Session API routes."""

import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from instructor.api.schemas import (
    ActivityResponse,
    ActivityResultResponse,
    SessionResponse,
    SessionSummaryResponse,
    StartSessionRequest,
    SubmitResponseRequest,
)
from instructor.db import get_db
from instructor.evaluator.scoring import score_exact_match
from instructor.learner.queries import load_learner_model
from instructor.models.session import Session
from instructor.practice.adaptive import select_exercises
from instructor.session.manager import (
    ActivityResult,
    SessionPlan,
    compute_summary,
    plan_session,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _get_active_sessions(request: Request) -> dict[uuid.UUID, SessionPlan]:
    """Get the in-memory session plan store, creating it if needed."""
    if not hasattr(request.app.state, "active_sessions"):
        request.app.state.active_sessions = {}
    result: dict[uuid.UUID, SessionPlan] = request.app.state.active_sessions
    return result


@router.post("", response_model=SessionResponse, status_code=201)
async def start_session(
    body: StartSessionRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Start a new learning session."""
    try:
        model = await load_learner_model(db, body.learner_id, body.language)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    exercises = select_exercises(model, count=15)
    plan = plan_session(model, exercises)

    session = Session(
        learner_id=body.learner_id,
        language=body.language,
        session_type=plan.session_type,
        started_at=plan.started_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    active_sessions = _get_active_sessions(request)
    active_sessions[session.id] = plan

    return SessionResponse(
        id=session.id,
        session_type=plan.session_type,
        started_at=plan.started_at,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    """Get session status."""
    session = await db.get(Session, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return SessionResponse(
        id=session.id,
        session_type=session.session_type,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )


@router.get("/{session_id}/next", response_model=ActivityResponse)
async def next_activity(
    session_id: uuid.UUID,
    request: Request,
) -> ActivityResponse:
    """Get the next activity in the session."""
    active_sessions = _get_active_sessions(request)
    plan = active_sessions.get(session_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    exercise = plan.next_exercise()
    if exercise is None:
        raise HTTPException(status_code=404, detail="Session is complete")

    return ActivityResponse(
        index=plan.current_index,
        exercise_type=exercise.exercise_type,
        prompt=exercise.prompt,
        options=exercise.options,
    )


@router.post(
    "/{session_id}/submit",
    response_model=ActivityResultResponse,
)
async def submit_response(
    session_id: uuid.UUID,
    body: SubmitResponseRequest,
    request: Request,
) -> ActivityResultResponse:
    """Submit a response to the current activity."""
    active_sessions = _get_active_sessions(request)
    plan = active_sessions.get(session_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    exercise = plan.next_exercise()
    if exercise is None:
        raise HTTPException(status_code=400, detail="Session is complete")

    result = score_exact_match(body.response, exercise.expected_response)

    plan.record_result(
        ActivityResult(
            activity_index=plan.current_index,
            exercise_type=exercise.exercise_type,
            prompt=exercise.prompt,
            response=body.response,
            score=result.score,
            correct=result.correct,
            feedback=result.feedback,
            time_taken_ms=body.time_taken_ms,
        )
    )

    return ActivityResultResponse(
        score=result.score,
        correct=result.correct,
        feedback=result.feedback,
    )


@router.post(
    "/{session_id}/end",
    response_model=SessionSummaryResponse,
)
async def end_session(
    session_id: uuid.UUID,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionSummaryResponse:
    """End a session and get summary."""
    active_sessions = _get_active_sessions(request)
    plan = active_sessions.get(session_id)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

    summary = compute_summary(plan)

    session = await db.get(Session, session_id)
    if session is not None:
        session.ended_at = datetime.now(UTC)
        session.performance_summary = {
            "total_activities": summary.total_activities,
            "correct_count": summary.correct_count,
            "incorrect_count": summary.incorrect_count,
            "accuracy": summary.accuracy,
        }
        await db.commit()

    del active_sessions[session_id]

    return SessionSummaryResponse(
        total_activities=summary.total_activities,
        correct_count=summary.correct_count,
        incorrect_count=summary.incorrect_count,
        accuracy=summary.accuracy,
    )
