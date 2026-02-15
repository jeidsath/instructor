"""Rule-based scoring for exercises with deterministic answers.

Provides scoring functions for exact match, form match, synonym match,
parsing (partial credit), and fill-in-the-blank exercises.  All text
comparisons are case-insensitive, whitespace-normalized, and
diacritic-insensitive (macrons, accents, breathing marks).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScoreResult:
    """Outcome of scoring a single exercise response."""

    score: float  # 0.0 – 1.0
    correct: bool
    feedback: str
    expected: str


# ------------------------------------------------------------------
# Text normalization
# ------------------------------------------------------------------

_WHITESPACE_RE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Lowercase, strip, collapse whitespace, remove diacritics."""
    text = text.strip().lower()
    text = _WHITESPACE_RE.sub(" ", text)
    # Decompose into base characters + combining marks, then remove
    # combining marks (category M) to strip accents/macrons/breathings.
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


# ------------------------------------------------------------------
# Scoring functions
# ------------------------------------------------------------------


def score_exact_match(response: str, expected: str) -> ScoreResult:
    """Case-insensitive, whitespace-normalized, diacritic-insensitive match."""
    norm_resp = _normalize(response)
    norm_exp = _normalize(expected)
    if norm_resp == norm_exp:
        return ScoreResult(
            score=1.0, correct=True, feedback="Correct!", expected=expected
        )
    return ScoreResult(
        score=0.0,
        correct=False,
        feedback=f"Expected: {expected}",
        expected=expected,
    )


def score_form_match(
    response: str,
    *,
    expected_lemma: str,
    valid_forms: list[str],
) -> ScoreResult:
    """Check if *response* is any valid form of the lemma.

    Parameters
    ----------
    response:
        The learner's answer.
    expected_lemma:
        The dictionary form shown as the expected answer on failure.
    valid_forms:
        All accepted inflected forms (provided by the caller; when the
        NLP morphology module is available it will generate these).
    """
    norm_resp = _normalize(response)
    if not norm_resp:
        return ScoreResult(
            score=0.0,
            correct=False,
            feedback=f"Expected a form of: {expected_lemma}",
            expected=expected_lemma,
        )
    for form in valid_forms:
        if _normalize(form) == norm_resp:
            return ScoreResult(
                score=1.0,
                correct=True,
                feedback="Correct!",
                expected=expected_lemma,
            )
    return ScoreResult(
        score=0.0,
        correct=False,
        feedback=f"Expected a form of: {expected_lemma}",
        expected=expected_lemma,
    )


def score_synonym_match(
    response: str,
    *,
    expected: str,
    synonyms: list[str],
) -> ScoreResult:
    """Accept *expected* or any of *synonyms* (case-insensitive)."""
    norm_resp = _normalize(response)
    if not norm_resp:
        return ScoreResult(
            score=0.0,
            correct=False,
            feedback=f"Expected: {expected}",
            expected=expected,
        )
    candidates = [expected, *synonyms]
    for candidate in candidates:
        if _normalize(candidate) == norm_resp:
            return ScoreResult(
                score=1.0,
                correct=True,
                feedback="Correct!",
                expected=expected,
            )
    return ScoreResult(
        score=0.0,
        correct=False,
        feedback=f"Expected: {expected}",
        expected=expected,
    )


def score_parsing(
    response: dict[str, str],
    expected: dict[str, str],
) -> ScoreResult:
    """Partial credit for multi-field parsing answers.

    Score = correct fields / total expected fields.
    Only fields present in *expected* are evaluated; extra fields in
    *response* are ignored.
    """
    if not expected:
        return ScoreResult(
            score=1.0, correct=True, feedback="No fields to check.", expected=""
        )

    total = len(expected)
    wrong_fields: list[str] = []
    for field_name, exp_val in expected.items():
        resp_val = response.get(field_name, "")
        if _normalize(str(resp_val)) != _normalize(str(exp_val)):
            wrong_fields.append(field_name)

    correct_count = total - len(wrong_fields)
    score = correct_count / total
    is_correct = len(wrong_fields) == 0

    if is_correct:
        feedback = "Correct!"
    else:
        parts = ", ".join(f"{f}: expected '{expected[f]}'" for f in wrong_fields)
        feedback = f"Incorrect fields — {parts}"

    expected_str = ", ".join(f"{k}={v}" for k, v in expected.items())
    return ScoreResult(
        score=score,
        correct=is_correct,
        feedback=feedback,
        expected=expected_str,
    )


def score_fill_blank(
    response: str,
    *,
    expected_form: str,
    valid_forms: list[str],
) -> ScoreResult:
    """Form matching for fill-in-the-blank exercises.

    Parameters
    ----------
    response:
        The learner's answer.
    expected_form:
        The primary expected form (shown on failure).
    valid_forms:
        All morphologically acceptable forms.
    """
    norm_resp = _normalize(response)
    if not norm_resp:
        return ScoreResult(
            score=0.0,
            correct=False,
            feedback=f"Expected: {expected_form}",
            expected=expected_form,
        )
    for form in valid_forms:
        if _normalize(form) == norm_resp:
            return ScoreResult(
                score=1.0,
                correct=True,
                feedback="Correct!",
                expected=expected_form,
            )
    return ScoreResult(
        score=0.0,
        correct=False,
        feedback=f"Expected: {expected_form}",
        expected=expected_form,
    )
