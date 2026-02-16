"""Adaptive exercise selection based on learner state.

Selects a mix of exercises from the learner's vocabulary and grammar,
prioritizing spaced repetition due items and balancing difficulty.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from instructor.nlp.morphology import flatten_forms
from instructor.practice.exercises import (
    GeneratedExercise,
    generate_definition_recall,
    generate_definition_recognition,
    generate_fill_blank,
    generate_form_identification,
    generate_form_production,
    select_distractors,
)

if TYPE_CHECKING:
    from datetime import datetime

    from instructor.learner.model import LearnerModel

# Difficulty mix: current level, stretch, review
MIX_CURRENT: float = 0.70
MIX_STRETCH: float = 0.20
MIX_REVIEW: float = 0.10


def select_exercises(
    model: LearnerModel,
    count: int = 10,
    *,
    now: datetime | None = None,
) -> list[GeneratedExercise]:
    """Select a balanced set of exercises for the learner.

    Priority order:
    1. Vocabulary due for spaced repetition review
    2. Weak vocabulary (low strength)
    3. New vocabulary from current level
    4. Grammar form drills

    The mix targets ~70% current level, ~20% stretch, ~10% review.
    """
    exercises: list[GeneratedExercise] = []

    # Gather all definitions for distractor pool.
    all_definitions = [
        v.vocabulary_item.definition
        for v in model.vocabulary
        if hasattr(v, "vocabulary_item") and v.vocabulary_item is not None
    ]

    # 1. Due items (review)
    due = model.vocabulary_due_for_review(now=now)
    for lv in due[:count]:
        if len(exercises) >= count:
            break
        item = getattr(lv, "vocabulary_item", None)
        if item is None:
            continue
        lang = model.language.value
        ex = _vocab_exercise(
            item.lemma,
            item.definition,
            item.forms,
            all_definitions,
            lang,
        )
        exercises.append(ex)

    # 2. Weak items (current level practice)
    weak = model.weak_vocabulary()
    for lv in weak:
        if len(exercises) >= count:
            break
        item = getattr(lv, "vocabulary_item", None)
        if item is None:
            continue
        lang = model.language.value
        ex = _vocab_exercise(
            item.lemma,
            item.definition,
            item.forms,
            all_definitions,
            lang,
        )
        exercises.append(ex)

    # 3. Strong items (review mix)
    strong = model.strong_vocabulary()
    review_count = max(1, int(count * MIX_REVIEW))
    for lv in strong[:review_count]:
        if len(exercises) >= count:
            break
        item = getattr(lv, "vocabulary_item", None)
        if item is None:
            continue
        exercises.append(
            generate_definition_recall(
                lemma=item.lemma,
                definition=item.definition,
                language=model.language.value,
            )
        )

    # 4. Fill remaining with grammar form drills
    for lg in model.grammar:
        if len(exercises) >= count:
            break
        # Find the concept for this grammar record
        concept = None
        for gc in model.grammar_concepts:
            if gc.id == lg.grammar_concept_id:
                concept = gc
                break
        if concept is None:
            continue
        exercises.append(
            generate_fill_blank(
                sentence_with_blank=f"[{concept.name}] exercise: ___",
                expected_form="",
                hint=concept.name,
                language=model.language.value,
            )
        )

    random.shuffle(exercises)
    return exercises[:count]


def _vocab_exercise(
    lemma: str,
    definition: str,
    forms: dict[str, object] | None,
    all_definitions: list[str],
    language: str,
) -> GeneratedExercise:
    """Generate a random vocabulary exercise type."""
    # If forms exist, sometimes do form-based exercises
    available_forms = flatten_forms(forms)
    exercise_types = ["definition_recall", "definition_recognition"]
    if available_forms:
        exercise_types.extend(["form_production", "form_identification"])

    choice = random.choice(exercise_types)

    if choice == "definition_recall":
        return generate_definition_recall(
            lemma=lemma, definition=definition, language=language
        )
    if choice == "definition_recognition":
        distractors = select_distractors(
            correct_definition=definition,
            all_definitions=all_definitions,
        )
        return generate_definition_recognition(
            lemma=lemma,
            definition=definition,
            distractors=distractors,
            language=language,
        )
    if choice == "form_production" and available_forms:
        form_str, features = random.choice(available_forms)
        return generate_form_production(
            lemma=lemma,
            target_features=features,
            expected_form=form_str,
            language=language,
        )
    # form_identification
    if available_forms:
        form_str, features = random.choice(available_forms)
        return generate_form_identification(
            form=form_str,
            lemma=lemma,
            expected_parse=features,
            language=language,
        )
    # Fallback
    return generate_definition_recall(
        lemma=lemma, definition=definition, language=language
    )
