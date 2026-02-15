"""Error explanation and on-demand concept explanations.

Uses Claude to generate pedagogical feedback on errors and
concept explanations tailored to the learner's context.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from instructor.ai.prompts import SYSTEM_PROMPT

if TYPE_CHECKING:
    from instructor.ai.client import AIClient

ERROR_EXPLANATION_PROMPT = """\
A {language} learner made an error on this exercise:

Exercise type: {exercise_type}
Prompt: {prompt}
Learner's response: {response}
Expected answer: {expected}
Score: {score}

Explain why the answer was wrong and how to get it right.
Be encouraging but precise. Keep the explanation to 2-3 sentences.

Respond with JSON:
{{
  "explanation": "<pedagogical explanation>",
  "tip": "<one practical tip for remembering>"
}}"""

CONCEPT_EXPLANATION_PROMPT = """\
Explain this {language} grammar concept to a learner at level {level}:

Concept: {concept_name}
Context: {context}

Provide a clear, concise explanation (3-5 sentences) suitable for
the learner's level. Include one example sentence with translation.

Respond with JSON:
{{
  "explanation": "<clear explanation>",
  "example": "<example sentence — translation>"
}}"""


def explain_error(
    client: AIClient,
    *,
    language: str,
    exercise_type: str,
    prompt: str,
    response: str,
    expected: str,
    score: float,
) -> tuple[str, str]:
    """Generate an explanation of why the answer was wrong.

    Returns (explanation, tip) tuple.
    """
    user_prompt = ERROR_EXPLANATION_PROMPT.format(
        language=language,
        exercise_type=exercise_type,
        prompt=prompt,
        response=response,
        expected=expected,
        score=score,
    )
    data = client.complete_json(system=SYSTEM_PROMPT, user=user_prompt)
    return data.get("explanation", ""), data.get("tip", "")


def explain_concept(
    client: AIClient,
    *,
    language: str,
    concept_name: str,
    context: str = "",
    level: float = 3.0,
) -> tuple[str, str]:
    """Generate an on-demand concept explanation.

    Returns (explanation, example) tuple.
    """
    user_prompt = CONCEPT_EXPLANATION_PROMPT.format(
        language=language,
        concept_name=concept_name,
        context=context or "general overview",
        level=int(level),
    )
    data = client.complete_json(system=SYSTEM_PROMPT, user=user_prompt)
    return data.get("explanation", ""), data.get("example", "")
