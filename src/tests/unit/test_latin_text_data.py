"""Validation tests for Latin text corpus data."""

from __future__ import annotations

from pathlib import Path

import pytest

from instructor.curriculum.loader import load_all_texts
from instructor.curriculum.registry import CurriculumRegistry

CURRICULUM_PATH = Path("curriculum")


@pytest.fixture(scope="module")
def registry() -> CurriculumRegistry:
    return CurriculumRegistry(CURRICULUM_PATH)


@pytest.fixture(scope="module")
def latin_texts(registry: CurriculumRegistry) -> list:
    return registry.get_texts("latin")


@pytest.fixture(scope="module")
def grammar_concept_names(registry: CurriculumRegistry) -> set[str]:
    return {c.name for c in registry.get_grammar_concepts("latin")}


@pytest.mark.unit
class TestLatinTextLoading:
    """All Latin text YAML files parse successfully."""

    def test_texts_load_without_error(self) -> None:
        texts = load_all_texts(CURRICULUM_PATH, "latin")
        assert len(texts) > 0

    def test_graded_texts_present(self, latin_texts: list) -> None:
        graded = [t for t in latin_texts if t.difficulty <= 6]
        assert len(graded) >= 10

    def test_authentic_texts_present(self, latin_texts: list) -> None:
        authentic = [t for t in latin_texts if t.difficulty >= 7]
        assert len(authentic) >= 3


@pytest.mark.unit
class TestLatinTextRequiredFields:
    """Every text has required fields."""

    def test_all_have_title(self, latin_texts: list) -> None:
        for text in latin_texts:
            assert text.title, f"Text missing title: {text}"

    def test_all_have_language(self, latin_texts: list) -> None:
        for text in latin_texts:
            assert text.language == "latin"

    def test_all_have_difficulty(self, latin_texts: list) -> None:
        for text in latin_texts:
            assert 1 <= text.difficulty <= 10, (
                f"{text.title}: difficulty {text.difficulty} out of range"
            )

    def test_all_have_content(self, latin_texts: list) -> None:
        for text in latin_texts:
            assert text.content.strip(), f"{text.title}: empty content"

    def test_all_have_translation(self, latin_texts: list) -> None:
        for text in latin_texts:
            assert text.translation and text.translation.strip(), (
                f"{text.title}: missing translation"
            )


@pytest.mark.unit
class TestLatinTextPrerequisites:
    """Prerequisite grammar references resolve to real concepts."""

    def test_all_prerequisites_valid(
        self, latin_texts: list, grammar_concept_names: set[str]
    ) -> None:
        for text in latin_texts:
            if not text.prerequisite_grammar:
                continue
            for prereq in text.prerequisite_grammar:
                assert prereq in grammar_concept_names, (
                    f"{text.title}: unknown prerequisite '{prereq}'"
                )

    def test_all_grammar_notes_valid(
        self, latin_texts: list, grammar_concept_names: set[str]
    ) -> None:
        for text in latin_texts:
            if not text.grammar_notes:
                continue
            for note in text.grammar_notes:
                assert note.concept in grammar_concept_names, (
                    f"{text.title}: unknown grammar note concept '{note.concept}'"
                )


@pytest.mark.unit
class TestLatinTextDifficultyConsistency:
    """Difficulty levels are consistent with prerequisite grammar."""

    def test_level_01_texts_use_basic_grammar(self, latin_texts: list) -> None:
        """Texts at difficulty 1-2 should only use units 01-02 concepts."""
        advanced_concepts = {
            "Third Declension",
            "Third Declension i-Stems",
            "Fourth Declension",
            "Fifth Declension",
            "Perfect Active Indicative",
            "Pluperfect Active Indicative",
            "Future Perfect Active Indicative",
            "Present Passive Indicative",
            "Imperfect Passive Indicative",
            "Perfect Passive Indicative",
            "Present Active Subjunctive",
            "Imperfect Active Subjunctive",
            "Present Participle",
            "Perfect Passive Participle",
            "Result Clauses",
            "Purpose Clauses",
            "Temporal Clauses",
            "Causal Clauses",
            "Conditional Clauses",
            "Indirect Statement",
            "Indirect Question",
            "Indirect Command",
        }
        for text in latin_texts:
            if text.difficulty > 2:
                continue
            if not text.prerequisite_grammar:
                continue
            used_advanced = set(text.prerequisite_grammar) & advanced_concepts
            assert not used_advanced, (
                f"{text.title} (difficulty {text.difficulty}) uses "
                f"advanced concepts: {used_advanced}"
            )

    def test_difficulty_range_coverage(self, latin_texts: list) -> None:
        """At least three difficulty levels are represented."""
        levels = {t.difficulty for t in latin_texts}
        assert len(levels) >= 3, f"Only {len(levels)} difficulty levels: {levels}"

    def test_authentic_texts_have_author(self, latin_texts: list) -> None:
        """Authentic texts (difficulty >= 7) should have an author."""
        for text in latin_texts:
            if text.difficulty >= 7:
                assert text.author, f"{text.title}: authentic text missing author"


@pytest.mark.unit
class TestLatinTextAnnotations:
    """Vocabulary and grammar notes are well-formed."""

    def test_vocabulary_notes_have_word_and_note(self, latin_texts: list) -> None:
        for text in latin_texts:
            if not text.vocabulary_notes:
                continue
            for vn in text.vocabulary_notes:
                assert vn.word.strip(), f"{text.title}: empty vocabulary note word"
                assert vn.note.strip(), f"{text.title}: empty note for word '{vn.word}'"

    def test_grammar_notes_have_concept_and_note(self, latin_texts: list) -> None:
        for text in latin_texts:
            if not text.grammar_notes:
                continue
            for gn in text.grammar_notes:
                assert gn.concept.strip(), f"{text.title}: empty grammar note concept"
                assert gn.note.strip(), (
                    f"{text.title}: empty note for concept '{gn.concept}'"
                )

    def test_all_texts_have_annotations(self, latin_texts: list) -> None:
        """Every text should have at least vocabulary or grammar notes."""
        for text in latin_texts:
            has_vocab = text.vocabulary_notes and len(text.vocabulary_notes) > 0
            has_grammar = text.grammar_notes and len(text.grammar_notes) > 0
            assert has_vocab or has_grammar, f"{text.title}: text has no annotations"
