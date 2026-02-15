"""Instructor engine: selects topics and orchestrates lesson delivery.

The instructor determines what to teach next based on the learner's
current state and curriculum position, then generates lesson content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instructor.learner.model import LearnerModel
    from instructor.models.grammar import GrammarConcept


@dataclass(frozen=True, slots=True)
class Topic:
    """A topic selected for instruction."""

    topic_type: str  # "vocabulary" or "grammar"
    name: str
    description: str
    difficulty: int
    concept: GrammarConcept | None = None
    vocabulary_lemmas: list[str] = field(default_factory=list)


@dataclass(slots=True)
class LessonContent:
    """Generated lesson content ready for presentation."""

    title: str
    explanation: str
    examples: list[str] = field(default_factory=list)
    paradigm_table: dict[str, str] | None = None
    summary: str = ""
    practice_prompts: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class Lesson:
    """A complete lesson with topic and content."""

    topic: Topic
    content: LessonContent


def select_next_topic(model: LearnerModel) -> Topic | None:
    """Choose what to teach next based on curriculum position.

    Priority:
    1. Grammar concepts whose prerequisites are met (next_grammar_concepts)
    2. Weak vocabulary that needs reinforcement

    Returns None if nothing new is ready to teach.
    """
    # Check for available grammar concepts.
    available_concepts = model.next_grammar_concepts()
    if available_concepts:
        concept = available_concepts[0]
        return Topic(
            topic_type="grammar",
            name=concept.name,
            description=concept.description,
            difficulty=concept.difficulty_level,
            concept=concept,
        )

    # Check for weak vocabulary that could use a review lesson.
    weak = model.weak_vocabulary()
    if weak:
        lemmas = [
            getattr(getattr(v, "vocabulary_item", None), "lemma", "") for v in weak[:5]
        ]
        lemmas = [lem for lem in lemmas if lem]
        if lemmas:
            return Topic(
                topic_type="vocabulary",
                name="Vocabulary Review",
                description="Review and reinforce weak vocabulary items.",
                difficulty=1,
                vocabulary_lemmas=lemmas,
            )

    return None


def build_grammar_lesson(
    concept: GrammarConcept,
    model: LearnerModel,
) -> LessonContent:
    """Build lesson content for a grammar concept (template-based).

    For AI-generated content, the caller should use the generator module.
    This provides a structural template.
    """
    weakest = model.weakest_capacity()
    return LessonContent(
        title=concept.name,
        explanation=f"In this lesson, we will learn about {concept.name}. "
        f"{concept.description}",
        examples=[],
        summary=f"Key points: {concept.name} "
        f"({concept.category}/{concept.subcategory}). "
        f"Focus on {weakest} exercises.",
        practice_prompts=[
            f"Practice: Apply {concept.name} in a sentence.",
            f"Identify: Find examples of {concept.name} in a text.",
        ],
    )


def build_vocabulary_lesson(
    lemmas: list[str],
    model: LearnerModel,
) -> LessonContent:
    """Build lesson content for vocabulary review (template-based)."""
    return LessonContent(
        title="Vocabulary Review",
        explanation=f"Let's review these {len(lemmas)} vocabulary items: "
        + ", ".join(lemmas),
        examples=[],
        summary=f"Reviewed {len(lemmas)} items. Keep practicing!",
        practice_prompts=[f"Define: {lemma}" for lemma in lemmas],
    )
