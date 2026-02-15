"""AI-based exercise scoring using Claude."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from instructor.ai.prompts import (
    COMPOSITION_PROMPT,
    COMPREHENSION_PROMPT,
    SYSTEM_PROMPT,
    TRANSLATION_PROMPT,
)

if TYPE_CHECKING:
    from instructor.ai.client import AIClient


@dataclass(frozen=True, slots=True)
class ErrorDetail:
    """A single error identified in the learner's response."""

    error_type: str
    location: str
    error: str
    expected: str
    explanation: str


@dataclass(frozen=True, slots=True)
class AIScoreResult:
    """Outcome of AI-based scoring."""

    score: float  # 0.0 – 1.0
    raw_score: int  # 0 – 5
    max_score: int  # typically 5
    correct: bool
    feedback: str
    corrected_response: str
    errors: list[ErrorDetail] = field(default_factory=list)


def _parse_errors(raw_errors: list[dict[str, Any]]) -> list[ErrorDetail]:
    """Parse error dicts from AI response into ErrorDetail objects."""
    result: list[ErrorDetail] = []
    for err in raw_errors:
        result.append(
            ErrorDetail(
                error_type=err.get("type", "unknown"),
                location=err.get("location", ""),
                error=err.get("error", ""),
                expected=err.get("expected", ""),
                explanation=err.get("explanation", ""),
            )
        )
    return result


def _build_result(data: dict[str, Any]) -> AIScoreResult:
    """Convert parsed AI JSON into an AIScoreResult."""
    raw_score = int(data.get("score", 0))
    max_score = int(data.get("max_score", 5))
    normalized = raw_score / max_score if max_score > 0 else 0.0
    return AIScoreResult(
        score=normalized,
        raw_score=raw_score,
        max_score=max_score,
        correct=raw_score >= max_score * 0.8,
        feedback=data.get("feedback", ""),
        corrected_response=data.get("corrected_response", ""),
        errors=_parse_errors(data.get("errors", [])),
    )


def score_translation(
    client: AIClient,
    *,
    source: str,
    response: str,
    direction: str,
    language: str,
) -> AIScoreResult:
    """Score a translation exercise using AI.

    Parameters
    ----------
    client:
        The AI client to use for the API call.
    source:
        The source text to translate.
    response:
        The learner's translation.
    direction:
        E.g. "Latin to English" or "English to Greek".
    language:
        The classical language involved.
    """
    user_prompt = TRANSLATION_PROMPT.format(
        direction=direction,
        language=language,
        source=source,
        response=response,
    )
    data = client.complete_json(system=SYSTEM_PROMPT, user=user_prompt)
    return _build_result(data)


def score_composition(
    client: AIClient,
    *,
    prompt: str,
    response: str,
    language: str,
    level: str,
) -> AIScoreResult:
    """Score a free composition exercise using AI."""
    user_prompt = COMPOSITION_PROMPT.format(
        language=language,
        level=level,
        prompt=prompt,
        response=response,
    )
    data = client.complete_json(system=SYSTEM_PROMPT, user=user_prompt)
    return _build_result(data)


def score_comprehension(
    client: AIClient,
    *,
    passage: str,
    question: str,
    response: str,
    language: str,
) -> AIScoreResult:
    """Score a reading comprehension exercise using AI."""
    user_prompt = COMPREHENSION_PROMPT.format(
        language=language,
        passage=passage,
        question=question,
        response=response,
    )
    data = client.complete_json(system=SYSTEM_PROMPT, user=user_prompt)
    return _build_result(data)
