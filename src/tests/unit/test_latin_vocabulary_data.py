from pathlib import Path

import pytest

from instructor.curriculum.loader import load_vocabulary_set
from instructor.curriculum.registry import CurriculumRegistry
from instructor.curriculum.schemas import VocabularySetData

CURRICULUM_PATH = Path("curriculum")
LATIN_VOCAB_DIR = CURRICULUM_PATH / "latin" / "vocabulary"


@pytest.mark.unit
class TestCoreVocabFiles:
    """All core vocabulary YAML files parse and validate correctly."""

    @pytest.fixture(scope="class")
    def registry(self) -> CurriculumRegistry:
        return CurriculumRegistry(CURRICULUM_PATH)

    def test_all_files_load(self, registry: CurriculumRegistry) -> None:
        """All Latin vocabulary files load without error."""
        vocab_sets = registry.get_vocabulary_sets("latin")
        assert len(vocab_sets) >= 3  # core-001, core-002, theme-family

    def test_core_001_has_100_items(self) -> None:
        """core-001 contains exactly 100 vocabulary items."""
        vs = load_vocabulary_set(LATIN_VOCAB_DIR / "core-001-basic.yml")
        assert vs.set == "core-001"
        assert len(vs.items) == 100

    def test_core_002_has_150_items(self) -> None:
        """core-002 contains exactly 150 vocabulary items."""
        vs = load_vocabulary_set(LATIN_VOCAB_DIR / "core-002-common.yml")
        assert vs.set == "core-002"
        assert len(vs.items) == 150

    def test_theme_family_loads(self) -> None:
        """theme-family loads with at least 20 items."""
        vs = load_vocabulary_set(LATIN_VOCAB_DIR / "theme-family.yml")
        assert vs.set == "theme-family"
        assert len(vs.items) >= 20


@pytest.mark.unit
class TestVocabFieldCompleteness:
    """Every vocabulary item has all required fields."""

    @pytest.fixture(scope="class")
    def all_sets(self) -> list[VocabularySetData]:
        sets: list[VocabularySetData] = []
        for path in sorted(LATIN_VOCAB_DIR.glob("*.yml")):
            sets.append(load_vocabulary_set(path))
        return sets

    def test_all_items_have_required_fields(
        self, all_sets: list[VocabularySetData]
    ) -> None:
        """Every item has lemma, pos, definition, and difficulty."""
        for vs in all_sets:
            for item in vs.items:
                assert item.lemma, f"empty lemma in {vs.set}"
                assert item.pos, f"empty pos in {vs.set}"
                assert item.definition, f"empty definition in {vs.set}"
                assert 1 <= item.difficulty <= 10, (
                    f"difficulty {item.difficulty} out of range "
                    f"for {item.lemma} in {vs.set}"
                )

    def test_no_duplicate_lemmas_within_sets(
        self, all_sets: list[VocabularySetData]
    ) -> None:
        """No duplicate lemma+pos combinations within any single set."""
        for vs in all_sets:
            seen: set[tuple[str, str]] = set()
            for item in vs.items:
                key = (item.lemma, item.pos)
                assert key not in seen, (
                    f"duplicate {item.lemma} ({item.pos}) in {vs.set}"
                )
                seen.add(key)

    def test_valid_parts_of_speech(
        self, all_sets: list[VocabularySetData]
    ) -> None:
        """All parts of speech are valid enum values."""
        valid_pos = {
            "noun", "verb", "adjective", "adverb", "preposition",
            "conjunction", "particle", "pronoun", "interjection",
        }
        for vs in all_sets:
            for item in vs.items:
                assert item.pos in valid_pos, (
                    f"invalid pos '{item.pos}' for {item.lemma} in {vs.set}"
                )


@pytest.mark.unit
class TestCoreFrequencyRanks:
    """Core vocabulary sets have valid, sequential frequency ranks."""

    def test_core_001_ranks_sequential(self) -> None:
        """core-001 frequency ranks are 1-100 without gaps."""
        vs = load_vocabulary_set(LATIN_VOCAB_DIR / "core-001-basic.yml")
        ranks = [item.frequency_rank for item in vs.items]
        assert all(r is not None for r in ranks), "all items need frequency_rank"
        int_ranks = [r for r in ranks if r is not None]
        assert sorted(int_ranks) == list(range(1, 101))

    def test_core_002_ranks_sequential(self) -> None:
        """core-002 frequency ranks are 101-250 without gaps."""
        vs = load_vocabulary_set(LATIN_VOCAB_DIR / "core-002-common.yml")
        ranks = [item.frequency_rank for item in vs.items]
        assert all(r is not None for r in ranks), "all items need frequency_rank"
        int_ranks = [r for r in ranks if r is not None]
        assert sorted(int_ranks) == list(range(101, 251))

    def test_no_rank_overlap_between_core_sets(self) -> None:
        """No frequency rank appears in both core-001 and core-002."""
        vs1 = load_vocabulary_set(LATIN_VOCAB_DIR / "core-001-basic.yml")
        vs2 = load_vocabulary_set(LATIN_VOCAB_DIR / "core-002-common.yml")
        ranks1 = {item.frequency_rank for item in vs1.items}
        ranks2 = {item.frequency_rank for item in vs2.items}
        overlap = ranks1 & ranks2
        assert not overlap, f"overlapping ranks: {overlap}"


@pytest.mark.unit
class TestThematicSets:
    """Thematic vocabulary sets follow conventions."""

    def test_theme_family_no_frequency_rank_required(self) -> None:
        """Thematic sets may omit frequency_rank."""
        vs = load_vocabulary_set(LATIN_VOCAB_DIR / "theme-family.yml")
        # Thematic sets don't need frequency_rank — just verify they load
        assert vs.language == "latin"
        assert len(vs.items) >= 20
