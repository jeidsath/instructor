"""Prompt templates for AI-based exercise scoring."""

from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert in Ancient Greek and Latin with extensive experience in \
classical language pedagogy. You evaluate learner responses to language \
exercises with precision and helpful feedback.

Always respond with valid JSON matching the requested format. Do not include \
any text outside the JSON object."""

TRANSLATION_PROMPT = """\
Score this {direction} translation exercise.

Source language: {language}
Source text: {source}
Learner's translation: {response}

Evaluate the translation for:
1. Accuracy of meaning
2. Correct grammar and syntax
3. Appropriate vocabulary choices
4. Natural fluency in the target language

Respond with JSON:
{{
  "score": <integer 0-5>,
  "max_score": 5,
  "errors": [
    {{
      "type": "<grammar|vocabulary|meaning|style>",
      "location": "<where in the response>",
      "error": "<what is wrong>",
      "expected": "<what was expected>",
      "explanation": "<brief pedagogical explanation>"
    }}
  ],
  "corrected_response": "<corrected version of the learner's translation>",
  "feedback": "<1-2 sentence overall feedback>"
}}"""

COMPOSITION_PROMPT = """\
Score this free composition exercise.

Language: {language}
Learner level: {level}
Prompt given to learner: {prompt}
Learner's composition: {response}

Evaluate for:
1. Grammar correctness (morphology, syntax, agreement)
2. Vocabulary range and appropriateness
3. Coherence and relevance to the prompt
4. Complexity appropriate to the stated level

Respond with JSON:
{{
  "score": <integer 0-5>,
  "max_score": 5,
  "errors": [
    {{
      "type": "<grammar|vocabulary|meaning|style>",
      "location": "<where in the response>",
      "error": "<what is wrong>",
      "expected": "<what was expected>",
      "explanation": "<brief pedagogical explanation>"
    }}
  ],
  "corrected_response": "<corrected version>",
  "feedback": "<1-2 sentence overall feedback>"
}}"""

COMPREHENSION_PROMPT = """\
Score this reading comprehension exercise.

Language of the passage: {language}
Passage: {passage}
Question: {question}
Learner's answer: {response}

Evaluate whether the learner's answer:
1. Correctly addresses the question
2. Demonstrates understanding of the passage
3. Is supported by evidence from the text

Respond with JSON:
{{
  "score": <integer 0-5>,
  "max_score": 5,
  "errors": [
    {{
      "type": "<comprehension|inference|detail>",
      "location": "<relevant part of the passage>",
      "error": "<what was missed or wrong>",
      "expected": "<what was expected>",
      "explanation": "<brief pedagogical explanation>"
    }}
  ],
  "corrected_response": "<model answer>",
  "feedback": "<1-2 sentence overall feedback>"
}}"""
