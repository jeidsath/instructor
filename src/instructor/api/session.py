"""Session API routes."""

import uuid

from fastapi import APIRouter, HTTPException

from instructor.api.schemas import (
    ActivityResponse,
    ActivityResultResponse,
    SessionResponse,
    SessionSummaryResponse,
    StartSessionRequest,
    SubmitResponseRequest,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse, status_code=201)
async def start_session(request: StartSessionRequest) -> SessionResponse:
    """Start a new learning session."""
    # Placeholder — will wire up session manager + DB.
    msg = "Session creation not yet implemented"
    raise HTTPException(status_code=501, detail=msg)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: uuid.UUID) -> SessionResponse:
    """Get session status."""
    msg = f"Session {session_id} not found"
    raise HTTPException(status_code=404, detail=msg)


@router.get("/{session_id}/next", response_model=ActivityResponse)
async def next_activity(session_id: uuid.UUID) -> ActivityResponse:
    """Get the next activity in the session."""
    msg = f"Session {session_id} not found"
    raise HTTPException(status_code=404, detail=msg)


@router.post(
    "/{session_id}/submit",
    response_model=ActivityResultResponse,
)
async def submit_response(
    session_id: uuid.UUID, request: SubmitResponseRequest
) -> ActivityResultResponse:
    """Submit a response to the current activity."""
    msg = f"Session {session_id} not found"
    raise HTTPException(status_code=404, detail=msg)


@router.post(
    "/{session_id}/end",
    response_model=SessionSummaryResponse,
)
async def end_session(session_id: uuid.UUID) -> SessionSummaryResponse:
    """End a session and get summary."""
    msg = f"Session {session_id} not found"
    raise HTTPException(status_code=404, detail=msg)
