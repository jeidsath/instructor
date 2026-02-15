"""Exercise generation for vocabulary and grammar drills.

Generates exercise dicts (not ORM objects) suitable for presentation
to the learner and later scoring by the evaluator.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class GeneratedExercise:
    """A generated exercise ready for presentation."""

    exercise_type: str
    prompt: str
    expected_response: str
    options: list[str] = field(default_factory=list)  # for multiple-choice
    metadata: dict[str, Any] = field(default_factory=dict)


def generate_definition_recall(
    *,
    lemma: str,
    definition: str,
    language: str,
) -> GeneratedExercise:
    """Show word, learner provides definition."""
    return GeneratedExercise(
        exercise_type="definition_recall",
        prompt=f"What is the meaning of '{lemma}'?",
        expected_response=definition,
        metadata={"lemma": lemma, "language": language},
    )


def generate_definition_recognition(
    *,
    lemma: str,
    definition: str,
    distractors: list[str],
    language: str,
) -> GeneratedExercise:
    """Show word + multiple-choice definitions."""
    options = [definition, *distractors]
    random.shuffle(options)
    return GeneratedExercise(
        exercise_type="definition_recognition",
        prompt=f"Select the correct meaning of '{lemma}':",
        expected_response=definition,
        options=options,
        metadata={"lemma": lemma, "language": language},
    )


def generate_form_production(
    *,
    lemma: str,
    target_features: dict[str, str],
    expected_form: str,
    language: str,
) -> GeneratedExercise:
    """Show lemma + morphological specification, learner produces form."""
    feature_str = ", ".join(f"{k}: {v}" for k, v in target_features.items())
    return GeneratedExercise(
        exercise_type="form_production",
        prompt=f"Give the {feature_str} form of '{lemma}':",
        expected_response=expected_form,
        metadata={
            "lemma": lemma,
            "features": target_features,
            "language": language,
        },
    )


def generate_form_identification(
    *,
    form: str,
    lemma: str,
    expected_parse: dict[str, str],
    language: str,
) -> GeneratedExercise:
    """Show inflected form, learner identifies properties."""
    parse_str = ", ".join(f"{k}={v}" for k, v in expected_parse.items())
    return GeneratedExercise(
        exercise_type="form_identification",
        prompt=f"Identify the morphological properties of '{form}' (from {lemma}):",
        expected_response=parse_str,
        metadata={
            "form": form,
            "lemma": lemma,
            "expected_parse": expected_parse,
            "language": language,
        },
    )


def generate_fill_blank(
    *,
    sentence_with_blank: str,
    expected_form: str,
    hint: str = "",
    language: str,
) -> GeneratedExercise:
    """Sentence with blank, learner supplies correct form."""
    prompt = f"Fill in the blank: {sentence_with_blank}"
    if hint:
        prompt += f"\n(Hint: {hint})"
    return GeneratedExercise(
        exercise_type="fill_blank",
        prompt=prompt,
        expected_response=expected_form,
        metadata={"language": language, "hint": hint},
    )


def generate_translation(
    *,
    source_text: str,
    direction: str,
    language: str,
) -> GeneratedExercise:
    """Translation exercise (AI-scored)."""
    return GeneratedExercise(
        exercise_type="translation",
        prompt=f"Translate the following ({direction}):\n\n{source_text}",
        expected_response="",  # AI-scored, no single expected answer
        metadata={"direction": direction, "language": language},
    )


def select_distractors(
    *,
    correct_definition: str,
    all_definitions: list[str],
    count: int = 3,
) -> list[str]:
    """Pick *count* distractor definitions, excluding the correct one."""
    candidates = [d for d in all_definitions if d != correct_definition]
    return random.sample(candidates, min(count, len(candidates)))
