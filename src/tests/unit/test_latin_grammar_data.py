from pathlib import Path

import pytest

from instructor.curriculum.loader import (
    load_all_grammar,
    load_grammar_file,
    load_grammar_sequence,
)
from instructor.curriculum.registry import CurriculumRegistry
from instructor.curriculum.schemas import GrammarConceptData

CURRICULUM_PATH = Path("curriculum")
LATIN_GRAMMAR_DIR = CURRICULUM_PATH / "latin" / "grammar"


@pytest.mark.unit
class TestGrammarFilesLoad:
    """All grammar YAML files parse and validate correctly."""

    @pytest.fixture(scope="class")
    def registry(self) -> CurriculumRegistry:
        return CurriculumRegistry(CURRICULUM_PATH)

    @pytest.fixture(scope="class")
    def all_concepts(self) -> list[GrammarConceptData]:
        concepts, _ = load_all_grammar(CURRICULUM_PATH, "latin")
        return concepts

    def test_all_files_load_via_registry(self, registry: CurriculumRegistry) -> None:
        """All Latin grammar files load without error through the registry."""
        concepts = registry.get_grammar_concepts("latin")
        assert len(concepts) >= 20  # nouns + verbs + adjectives + pronouns + syntax

    def test_morphology_nouns_loads(self) -> None:
        """Nouns morphology file loads correctly."""
        grammar = load_grammar_file(LATIN_GRAMMAR_DIR / "morphology" / "nouns.yml")
        assert grammar.language == "latin"
        assert grammar.category == "morphology"
        assert len(grammar.concepts) >= 5  # 5 declensions + variants

    def test_morphology_verbs_loads(self) -> None:
        """Verbs morphology file loads correctly."""
        grammar = load_grammar_file(LATIN_GRAMMAR_DIR / "morphology" / "verbs.yml")
        assert grammar.language == "latin"
        assert grammar.category == "morphology"
        assert len(grammar.concepts) >= 10  # many tense/mood/voice combos

    def test_morphology_adjectives_loads(self) -> None:
        """Adjectives morphology file loads correctly."""
        grammar = load_grammar_file(LATIN_GRAMMAR_DIR / "morphology" / "adjectives.yml")
        assert grammar.language == "latin"
        assert len(grammar.concepts) >= 3

    def test_morphology_pronouns_loads(self) -> None:
        """Pronouns morphology file loads correctly."""
        grammar = load_grammar_file(LATIN_GRAMMAR_DIR / "morphology" / "pronouns.yml")
        assert grammar.language == "latin"
        assert len(grammar.concepts) >= 4

    def test_syntax_cases_loads(self) -> None:
        """Case usage syntax file loads correctly."""
        grammar = load_grammar_file(LATIN_GRAMMAR_DIR / "syntax" / "cases.yml")
        assert grammar.language == "latin"
        assert grammar.category == "syntax"
        assert len(grammar.concepts) >= 5

    def test_syntax_subordination_loads(self) -> None:
        """Subordination syntax file loads correctly."""
        grammar = load_grammar_file(LATIN_GRAMMAR_DIR / "syntax" / "subordination.yml")
        assert grammar.language == "latin"
        assert len(grammar.concepts) >= 4

    def test_syntax_indirect_discourse_loads(self) -> None:
        """Indirect discourse syntax file loads correctly."""
        grammar = load_grammar_file(
            LATIN_GRAMMAR_DIR / "syntax" / "indirect-discourse.yml"
        )
        assert grammar.language == "latin"
        assert len(grammar.concepts) >= 2


@pytest.mark.unit
class TestGrammarFieldCompleteness:
    """Every grammar concept has all required fields."""

    @pytest.fixture(scope="class")
    def all_concepts(self) -> list[GrammarConceptData]:
        concepts, _ = load_all_grammar(CURRICULUM_PATH, "latin")
        return concepts

    def test_all_concepts_have_required_fields(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
        """Every concept has name, subcategory, difficulty, description."""
        for c in all_concepts:
            assert c.name, "concept missing name"
            assert c.subcategory, f"concept {c.name} missing subcategory"
            assert 1 <= c.difficulty <= 10, (
                f"concept {c.name} difficulty {c.difficulty} out of range"
            )
            assert c.description, f"concept {c.name} missing description"

    def test_all_concepts_have_examples(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
        """Every concept has at least one example with latin and english."""
        for c in all_concepts:
            assert c.examples and len(c.examples) >= 1, (
                f"concept {c.name} has no examples"
            )
            for ex in c.examples:
                assert ex.latin or ex.greek, (
                    f"concept {c.name} example missing latin/greek text"
                )
                assert ex.english, (
                    f"concept {c.name} example missing english translation"
                )

    def test_no_duplicate_concept_names(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
        """No duplicate concept names across all grammar files."""
        names: set[str] = set()
        for c in all_concepts:
            assert c.name not in names, f"duplicate concept name: {c.name}"
            names.add(c.name)


@pytest.mark.unit
class TestPrerequisiteIntegrity:
    """Prerequisite references are valid and acyclic."""

    @pytest.fixture(scope="class")
    def all_concepts(self) -> list[GrammarConceptData]:
        # load_all_grammar validates prerequisites internally
        concepts, _ = load_all_grammar(CURRICULUM_PATH, "latin")
        return concepts

    def test_prerequisites_resolve(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
        """All prerequisite references resolve to existing concept names."""
        names = {c.name for c in all_concepts}
        for c in all_concepts:
            for prereq in c.prerequisites:
                assert prereq in names, (
                    f"concept {c.name} has unresolved prereq: {prereq}"
                )

    def test_dag_is_acyclic(self, all_concepts: list[GrammarConceptData]) -> None:
        """Prerequisite graph has no cycles (verified by loader)."""
        # load_all_grammar already validates this; if we got here, it passed
        assert len(all_concepts) > 0

    def test_difficulty_nondecreasing_along_prereqs(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
        """Difficulty should not decrease along prerequisite chains."""
        concept_map = {c.name: c for c in all_concepts}
        violations: list[str] = []
        for c in all_concepts:
            for prereq_name in c.prerequisites:
                prereq = concept_map.get(prereq_name)
                if prereq and prereq.difficulty > c.difficulty:
                    violations.append(
                        f"{c.name} (diff={c.difficulty}) requires "
                        f"{prereq_name} (diff={prereq.difficulty})"
                    )
        assert not violations, "Difficulty decreases along prereq chain:\n" + "\n".join(
            violations
        )


@pytest.mark.unit
class TestSequenceFile:
    """Grammar sequence file is consistent with concept definitions."""

    @pytest.fixture(scope="class")
    def all_concepts(self) -> list[GrammarConceptData]:
        concepts, _ = load_all_grammar(CURRICULUM_PATH, "latin")
        return concepts

    def test_sequence_loads(self) -> None:
        """Sequence file loads correctly."""
        seq = load_grammar_sequence(LATIN_GRAMMAR_DIR / "sequence.yml")
        assert seq.language == "latin"
        assert len(seq.sequence) >= 2

    def test_sequence_references_valid_concepts(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
        """Every concept referenced in the sequence exists in grammar files."""
        seq = load_grammar_sequence(LATIN_GRAMMAR_DIR / "sequence.yml")
        defined_names = {c.name for c in all_concepts}
        for unit in seq.sequence:
            for concept_name in unit.concepts:
                assert concept_name in defined_names, (
                    f"sequence unit {unit.unit} references undefined "
                    f"concept: {concept_name}"
                )

    def test_sequence_units_ordered(self) -> None:
        """Sequence units have ordered unit names."""
        seq = load_grammar_sequence(LATIN_GRAMMAR_DIR / "sequence.yml")
        unit_names = [u.unit for u in seq.sequence]
        assert unit_names == sorted(unit_names), (
            f"sequence units not in order: {unit_names}"
        )
