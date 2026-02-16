"""Validation tests for Greek text corpus data."""

from __future__ import annotations

import unicodedata
from pathlib import Path

import pytest

from instructor.curriculum.loader import load_all_texts
from instructor.curriculum.registry import CurriculumRegistry

CURRICULUM_PATH = Path("curriculum")


@pytest.fixture(scope="module")
def registry() -> CurriculumRegistry:
    return CurriculumRegistry(CURRICULUM_PATH)


@pytest.fixture(scope="module")
def greek_texts(registry: CurriculumRegistry) -> list:
    return registry.get_texts("greek")


@pytest.fixture(scope="module")
def grammar_concept_names(registry: CurriculumRegistry) -> set[str]:
    return {c.name for c in registry.get_grammar_concepts("greek")}


def _is_greek_text(text: str) -> bool:
    """Check that text contains Greek Unicode characters."""
    for ch in text:
        if unicodedata.category(ch).startswith("L"):
            name = unicodedata.name(ch, "")
            if "GREEK" in name:
                return True
    return False


@pytest.mark.unit
class TestGreekTextLoading:
    """All Greek text YAML files parse successfully."""

    def test_texts_load_without_error(self) -> None:
        texts = load_all_texts(CURRICULUM_PATH, "greek")
        assert len(texts) > 0

    def test_graded_texts_present(self, greek_texts: list) -> None:
        graded = [t for t in greek_texts if t.difficulty <= 6]
        assert len(graded) >= 10

    def test_authentic_texts_present(self, greek_texts: list) -> None:
        authentic = [t for t in greek_texts if t.difficulty >= 7]
        assert len(authentic) >= 3


@pytest.mark.unit
class TestGreekTextRequiredFields:
    """Every text has required fields."""

    def test_all_have_title(self, greek_texts: list) -> None:
        for text in greek_texts:
            assert text.title, f"Text missing title: {text}"

    def test_all_have_language(self, greek_texts: list) -> None:
        for text in greek_texts:
            assert text.language == "greek"

    def test_all_have_difficulty(self, greek_texts: list) -> None:
        for text in greek_texts:
            assert 1 <= text.difficulty <= 10, (
                f"{text.title}: difficulty {text.difficulty} out of range"
            )

    def test_all_have_content(self, greek_texts: list) -> None:
        for text in greek_texts:
            assert text.content.strip(), f"{text.title}: empty content"

    def test_all_have_translation(self, greek_texts: list) -> None:
        for text in greek_texts:
            assert text.translation and text.translation.strip(), (
                f"{text.title}: missing translation"
            )

    def test_content_is_greek_unicode(self, greek_texts: list) -> None:
        """Text content should contain valid Greek Unicode characters."""
        for text in greek_texts:
            assert _is_greek_text(text.content), (
                f"{text.title}: content does not contain Greek characters"
            )


@pytest.mark.unit
class TestGreekTextPrerequisites:
    """Prerequisite grammar references resolve to real concepts."""

    def test_all_prerequisites_valid(
        self, greek_texts: list, grammar_concept_names: set[str]
    ) -> None:
        for text in greek_texts:
            if not text.prerequisite_grammar:
                continue
            for prereq in text.prerequisite_grammar:
                assert prereq in grammar_concept_names, (
                    f"{text.title}: unknown prerequisite '{prereq}'"
                )

    def test_all_grammar_notes_valid(
        self, greek_texts: list, grammar_concept_names: set[str]
    ) -> None:
        for text in greek_texts:
            if not text.grammar_notes:
                continue
            for note in text.grammar_notes:
                assert note.concept in grammar_concept_names, (
                    f"{text.title}: unknown grammar note concept '{note.concept}'"
                )


@pytest.mark.unit
class TestGreekTextDifficultyConsistency:
    """Difficulty levels are consistent with prerequisites."""

    def test_difficulty_range_coverage(self, greek_texts: list) -> None:
        """At least three difficulty levels are represented."""
        levels = {t.difficulty for t in greek_texts}
        assert len(levels) >= 3, f"Only {len(levels)} difficulty levels: {levels}"

    def test_authentic_texts_have_author(self, greek_texts: list) -> None:
        """Authentic texts (difficulty >= 7) should have an author."""
        for text in greek_texts:
            if text.difficulty >= 7:
                assert text.author, f"{text.title}: authentic text missing author"

    def test_homeric_text_is_high_difficulty(self, greek_texts: list) -> None:
        """Homeric texts should be marked as high difficulty."""
        for text in greek_texts:
            if text.author and "Ὅμηρος" in text.author:
                assert text.difficulty >= 9, (
                    f"{text.title}: Homeric text should be difficulty >= 9"
                )


@pytest.mark.unit
class TestGreekTextAnnotations:
    """Vocabulary and grammar notes are well-formed."""

    def test_vocabulary_notes_have_word_and_note(self, greek_texts: list) -> None:
        for text in greek_texts:
            if not text.vocabulary_notes:
                continue
            for vn in text.vocabulary_notes:
                assert vn.word.strip(), f"{text.title}: empty vocabulary note word"
                assert vn.note.strip(), f"{text.title}: empty note for word '{vn.word}'"

    def test_grammar_notes_have_concept_and_note(self, greek_texts: list) -> None:
        for text in greek_texts:
            if not text.grammar_notes:
                continue
            for gn in text.grammar_notes:
                assert gn.concept.strip(), f"{text.title}: empty grammar note concept"
                assert gn.note.strip(), (
                    f"{text.title}: empty note for concept '{gn.concept}'"
                )

    def test_all_texts_have_annotations(self, greek_texts: list) -> None:
        """Every text should have at least vocabulary or grammar notes."""
        for text in greek_texts:
            has_vocab = text.vocabulary_notes and len(text.vocabulary_notes) > 0
            has_grammar = text.grammar_notes and len(text.grammar_notes) > 0
            assert has_vocab or has_grammar, f"{text.title}: text has no annotations"
