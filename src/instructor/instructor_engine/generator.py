"""AI-powered lesson content generation.

Uses Claude to generate contextual explanations, examples, and
paradigm tables adapted to the learner's level.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from instructor.ai.prompts import SYSTEM_PROMPT
from instructor.instructor_engine.engine import LessonContent

if TYPE_CHECKING:
    from instructor.ai.client import AIClient
    from instructor.models.grammar import GrammarConcept

GRAMMAR_LESSON_PROMPT = """\
Generate a lesson for the following grammar concept in {language}.

Concept: {name}
Category: {category}/{subcategory}
Description: {description}
Learner level: {level} (1=beginner, 10=advanced)

Provide:
1. A clear, concise explanation suitable for the learner's level
2. 3-5 example sentences with translations
3. A paradigm table if applicable (e.g. declension/conjugation)
4. A brief summary of key points

Respond with JSON:
{{
  "explanation": "<clear explanation>",
  "examples": ["<example 1>", "<example 2>", "..."],
  "paradigm_table": {{"<form_label>": "<form>", ...}} or null,
  "summary": "<brief summary>"
}}"""

VOCABULARY_LESSON_PROMPT = """\
Generate a vocabulary lesson for these {language} words:

Words: {words}
Learner level: {level} (1=beginner, 10=advanced)

For each word, provide:
1. Definition and usage notes
2. An example sentence with translation
3. Related words or cognates if helpful

Respond with JSON:
{{
  "explanation": "<overview of the vocabulary set>",
  "examples": ["<word1: example sentence — translation>", "..."],
  "summary": "<brief summary of key vocabulary>"
}}"""


def generate_grammar_lesson(
    client: AIClient,
    concept: GrammarConcept,
    *,
    language: str,
    level: float,
) -> LessonContent:
    """Generate an AI-powered grammar lesson."""
    user_prompt = GRAMMAR_LESSON_PROMPT.format(
        language=language,
        name=concept.name,
        category=concept.category,
        subcategory=concept.subcategory,
        description=concept.description,
        level=int(level),
    )
    data = client.complete_json(system=SYSTEM_PROMPT, user=user_prompt)
    paradigm = data.get("paradigm_table")
    return LessonContent(
        title=concept.name,
        explanation=data.get("explanation", ""),
        examples=data.get("examples", []),
        paradigm_table=paradigm if isinstance(paradigm, dict) else None,
        summary=data.get("summary", ""),
    )


def generate_vocabulary_lesson(
    client: AIClient,
    lemmas: list[str],
    *,
    language: str,
    level: float,
) -> LessonContent:
    """Generate an AI-powered vocabulary lesson."""
    user_prompt = VOCABULARY_LESSON_PROMPT.format(
        language=language,
        words=", ".join(lemmas),
        level=int(level),
    )
    data = client.complete_json(system=SYSTEM_PROMPT, user=user_prompt)
    return LessonContent(
        title="Vocabulary Lesson",
        explanation=data.get("explanation", ""),
        examples=data.get("examples", []),
        summary=data.get("summary", ""),
    )
