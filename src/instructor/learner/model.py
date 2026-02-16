"""Aggregate read-only view of a learner's state in one language.

The ``LearnerModel`` is the primary interface used by the instructor,
evaluator, and practice engine to make pedagogical decisions.  It is
constructed from pre-loaded database records and exposes convenience
methods for querying vocabulary strength, grammar mastery, and
recommended next actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instructor.models.grammar import GrammarConcept, LearnerGrammar
    from instructor.models.learner import Learner, LearnerLanguageState
    from instructor.models.vocabulary import LearnerVocabulary

from instructor.models.enums import Language, MasteryLevel, SessionType

# Number of overdue vocabulary items that triggers a review session.
REVIEW_THRESHOLD: int = 5


@dataclass
class LearnerModel:
    """Aggregate view of a learner's state in one language."""

    learner: Learner
    language: Language
    state: LearnerLanguageState
    vocabulary: list[LearnerVocabulary] = field(default_factory=list)
    grammar: list[LearnerGrammar] = field(default_factory=list)
    grammar_concepts: list[GrammarConcept] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Vocabulary queries
    # ------------------------------------------------------------------

    def vocabulary_due_for_review(
        self,
        *,
        now: datetime | None = None,
    ) -> list[LearnerVocabulary]:
        """Items where ``next_review <= now``, ordered by most overdue first."""
        if now is None:
            now = datetime.now(UTC)
        due = [
            v
            for v in self.vocabulary
            if v.next_review is not None and v.next_review <= now
        ]
        due.sort(key=lambda v: v.next_review)  # type: ignore[arg-type, return-value]
        return due

    def weak_vocabulary(self, threshold: float = 0.3) -> list[LearnerVocabulary]:
        """Items with strength below *threshold*."""
        return [v for v in self.vocabulary if v.strength < threshold]

    def strong_vocabulary(self, threshold: float = 0.7) -> list[LearnerVocabulary]:
        """Items with strength above *threshold*."""
        return [v for v in self.vocabulary if v.strength > threshold]

    # ------------------------------------------------------------------
    # Grammar queries
    # ------------------------------------------------------------------

    def grammar_at_level(self, level: MasteryLevel) -> list[LearnerGrammar]:
        """Grammar items at exactly *level*."""
        return [g for g in self.grammar if g.mastery_level == level]

    def next_grammar_concepts(self) -> list[GrammarConcept]:
        """Concepts whose prerequisites are all met but not yet introduced.

        A concept is eligible when:
        - The learner has no record for it, or it is at UNKNOWN level.
        - Every prerequisite concept is at mastery level >= PROFICIENT.
        """
        # Build lookup: concept name → learner mastery level.
        mastery_by_name: dict[str, MasteryLevel] = {}
        concept_id_to_name: dict[object, str] = {}
        for gc in self.grammar_concepts:
            concept_id_to_name[gc.id] = gc.name
        for lg in self.grammar:
            name = concept_id_to_name.get(lg.grammar_concept_id)
            if name is not None:
                mastery_by_name[name] = lg.mastery_level

        # Names the learner has already been introduced to.
        introduced = {
            name
            for name, level in mastery_by_name.items()
            if level.value >= MasteryLevel.INTRODUCED.value
        }

        eligible: list[GrammarConcept] = []
        for gc in self.grammar_concepts:
            if gc.name in introduced:
                continue
            prereqs = gc.prerequisite_ids or []
            if all(
                mastery_by_name.get(p, MasteryLevel.UNKNOWN).value
                >= MasteryLevel.PROFICIENT.value
                for p in prereqs
            ):
                eligible.append(gc)
        return eligible

    # ------------------------------------------------------------------
    # Capacity queries
    # ------------------------------------------------------------------

    def weakest_capacity(self) -> str:
        """Return the name of the capacity with the lowest level.

        On ties, returns the first in canonical order:
        reading, writing, listening, speaking.
        """
        capacities = [
            ("reading", self.state.reading_level),
            ("writing", self.state.writing_level),
            ("listening", self.state.listening_level),
            ("speaking", self.state.speaking_level),
        ]
        return min(capacities, key=lambda c: c[1])[0]

    # ------------------------------------------------------------------
    # Session recommendation
    # ------------------------------------------------------------------

    def recommended_session_type(
        self,
        *,
        now: datetime | None = None,
    ) -> SessionType:
        """Suggest what the learner should do next.

        - PLACEMENT if the learner has never had a session.
        - PRACTICE if vocabulary items are due for review.
        - LESSON if new grammar concepts are available.
        - PRACTICE as a fallback.
        """
        if self.state.last_session_at is None:
            return SessionType.PLACEMENT

        due = self.vocabulary_due_for_review(now=now)
        if len(due) >= REVIEW_THRESHOLD:
            return SessionType.PRACTICE

        if self.next_grammar_concepts():
            return SessionType.LESSON

        return SessionType.PRACTICE
