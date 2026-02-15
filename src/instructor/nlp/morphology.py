"""Morphological analysis and generation for Latin and Greek.

Uses paradigm tables from curriculum vocabulary data to look up forms.
The ``forms`` field on :class:`VocabularyItem` stores nested dicts
mapping category → slot → inflected form.  This module flattens those
tables for lookup.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MorphologicalAnalysis:
    """Result of analyzing a single form."""

    lemma: str
    form: str
    features: dict[str, str]  # e.g. {"tense": "present", "person": "1s"}


def _strip_diacritics(text: str) -> str:
    """Remove combining marks (accents, macrons, breathing)."""
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _normalize(text: str) -> str:
    return _strip_diacritics(text.strip().lower())


def flatten_forms(forms: dict[str, Any] | None) -> list[tuple[str, dict[str, str]]]:
    """Flatten nested form tables into (form_string, features) pairs.

    Handles both flat dicts (``{"nominative_singular": "rosa"}``)
    and nested dicts (``{"present_active_indicative": {"1s": "amō"}}``).
    """
    if not forms:
        return []

    result: list[tuple[str, dict[str, str]]] = []
    for key, value in forms.items():
        if isinstance(value, dict):
            for slot, form_str in value.items():
                if isinstance(form_str, str):
                    result.append((form_str, {"category": key, "slot": slot}))
        elif isinstance(value, str):
            result.append((value, {"slot": key}))
    return result


def extract_all_forms(forms: dict[str, Any] | None) -> list[str]:
    """Return all unique inflected forms from a form table."""
    return list({form_str for form_str, _ in flatten_forms(forms)})


def is_valid_form_of(
    form: str,
    lemma: str,
    forms_table: dict[str, Any] | None,
) -> bool:
    """Check whether *form* is the lemma or any inflected form.

    Comparison is case-insensitive and diacritic-insensitive.
    """
    norm_form = _normalize(form)
    if not norm_form:
        return False

    # Check against the lemma itself.
    if norm_form == _normalize(lemma):
        return True

    # Check against all forms in the table.
    for form_str, _ in flatten_forms(forms_table):
        if _normalize(form_str) == norm_form:
            return True
    return False


def analyze_form(
    form: str,
    lemma: str,
    forms_table: dict[str, Any] | None,
) -> list[MorphologicalAnalysis]:
    """Find all matching analyses for *form* in the paradigm of *lemma*.

    Returns an empty list if the form is not found.
    """
    norm_form = _normalize(form)
    if not norm_form:
        return []

    results: list[MorphologicalAnalysis] = []

    # Check the lemma itself (citation form).
    if norm_form == _normalize(lemma):
        results.append(
            MorphologicalAnalysis(lemma=lemma, form=form, features={"slot": "lemma"})
        )

    for form_str, features in flatten_forms(forms_table):
        if _normalize(form_str) == norm_form:
            results.append(
                MorphologicalAnalysis(lemma=lemma, form=form_str, features=features)
            )
    return results


def generate_form(
    lemma: str,
    features: dict[str, str],
    forms_table: dict[str, Any] | None,
) -> str | None:
    """Produce the inflected form matching *features*, or ``None``.

    Parameters
    ----------
    lemma:
        The dictionary form.
    features:
        Keys to match against the paradigm table.
        For nested tables, provide ``category`` and ``slot``.
        For flat tables, provide ``slot``.
    forms_table:
        The paradigm table from the vocabulary item.
    """
    if not forms_table:
        return None

    category = features.get("category")
    slot = features.get("slot")

    if category and slot:
        subtable = forms_table.get(category)
        if isinstance(subtable, dict):
            result = subtable.get(slot)
            if isinstance(result, str):
                return result
    elif slot:
        result = forms_table.get(slot)
        if isinstance(result, str):
            return result

    return None
