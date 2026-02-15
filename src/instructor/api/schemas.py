"""Pydantic request/response models for API endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from instructor.models.enums import Language, MasteryLevel, SessionType

# ------------------------------------------------------------------
# Learner
# ------------------------------------------------------------------


class CreateLearnerRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class LearnerResponse(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class LearnerStateResponse(BaseModel):
    language: Language
    reading_level: float
    writing_level: float
    listening_level: float
    speaking_level: float
    active_vocabulary_size: int
    grammar_concepts_mastered: int
    last_session_at: datetime | None
    total_study_time_minutes: int

    model_config = {"from_attributes": True}


class VocabularyItemResponse(BaseModel):
    lemma: str
    definition: str
    strength: float
    next_review: datetime | None
    times_correct: int
    times_incorrect: int


class GrammarItemResponse(BaseModel):
    concept_name: str
    mastery_level: MasteryLevel
    times_practiced: int
    recent_error_rate: float


# ------------------------------------------------------------------
# Session
# ------------------------------------------------------------------


class StartSessionRequest(BaseModel):
    learner_id: uuid.UUID
    language: Language


class SessionResponse(BaseModel):
    id: uuid.UUID
    session_type: SessionType
    started_at: datetime
    ended_at: datetime | None = None


class ActivityResponse(BaseModel):
    index: int
    exercise_type: str
    prompt: str
    options: list[str] = Field(default_factory=list)


class SubmitResponseRequest(BaseModel):
    response: str
    time_taken_ms: int = 0


class ActivityResultResponse(BaseModel):
    score: float
    correct: bool
    feedback: str


class SessionSummaryResponse(BaseModel):
    total_activities: int
    correct_count: int
    incorrect_count: int
    accuracy: float


# ------------------------------------------------------------------
# Curriculum
# ------------------------------------------------------------------


class CurriculumUnitResponse(BaseModel):
    unit_number: int
    name: str
    concept_count: int


class VocabularySetResponse(BaseModel):
    set_name: str
    language: Language
    item_count: int


class GrammarConceptResponse(BaseModel):
    name: str
    category: str
    subcategory: str
    difficulty_level: int
    prerequisite_names: list[str] = Field(default_factory=list)


# ------------------------------------------------------------------
# Placement
# ------------------------------------------------------------------


class StartPlacementRequest(BaseModel):
    learner_id: uuid.UUID
    language: Language


class PlacementResponseItem(BaseModel):
    probe_type: str
    difficulty: int
    correct: bool
    item_id: str = ""


class PlacementSubmitRequest(BaseModel):
    responses: list[PlacementResponseItem]


class PlacementResultResponse(BaseModel):
    total_score: float
    vocabulary_score: float
    grammar_score: float
    reading_score: float
    starting_unit: int
