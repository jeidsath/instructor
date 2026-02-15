from pathlib import Path

from instructor.curriculum.loader import (
    load_all_grammar,
    load_all_texts,
    load_all_vocabulary,
)
from instructor.curriculum.schemas import (
    GrammarConceptData,
    GrammarSequenceData,
    TextEntryData,
    VocabularySetData,
)


class CurriculumRegistry:
    """Immutable registry of all curriculum content, loaded at startup."""

    def __init__(self, base_path: Path) -> None:
        self._vocabulary: dict[str, list[VocabularySetData]] = {}
        self._grammar_concepts: dict[str, list[GrammarConceptData]] = {}
        self._grammar_sequences: dict[str, GrammarSequenceData | None] = {}
        self._texts: dict[str, list[TextEntryData]] = {}

        for language in ("greek", "latin"):
            lang_dir = base_path / language
            if not lang_dir.exists():
                continue
            self._vocabulary[language] = load_all_vocabulary(base_path, language)
            concepts, sequence = load_all_grammar(base_path, language)
            self._grammar_concepts[language] = concepts
            self._grammar_sequences[language] = sequence
            self._texts[language] = load_all_texts(base_path, language)

    def get_vocabulary_sets(self, language: str) -> list[VocabularySetData]:
        return self._vocabulary.get(language, [])

    def get_grammar_concepts(self, language: str) -> list[GrammarConceptData]:
        return self._grammar_concepts.get(language, [])

    def get_grammar_sequence(self, language: str) -> GrammarSequenceData | None:
        return self._grammar_sequences.get(language)

    def get_texts(
        self,
        language: str,
        difficulty_range: tuple[int, int] | None = None,
    ) -> list[TextEntryData]:
        texts = self._texts.get(language, [])
        if difficulty_range is not None:
            lo, hi = difficulty_range
            texts = [t for t in texts if lo <= t.difficulty <= hi]
        return texts
