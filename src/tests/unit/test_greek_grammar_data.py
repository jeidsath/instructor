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
GREEK_GRAMMAR_DIR = CURRICULUM_PATH / "greek" / "grammar"


@pytest.mark.unit
class TestGrammarFilesLoad:
    """All grammar YAML files parse and validate correctly."""

    @pytest.fixture(scope="class")
    def registry(self) -> CurriculumRegistry:
        return CurriculumRegistry(CURRICULUM_PATH)

    @pytest.fixture(scope="class")
    def all_concepts(self) -> list[GrammarConceptData]:
        concepts, _ = load_all_grammar(CURRICULUM_PATH, "greek")
        return concepts

    def test_all_files_load_via_registry(self, registry: CurriculumRegistry) -> None:
        """All Greek grammar files load without error through the registry."""
        concepts = registry.get_grammar_concepts("greek")
        assert len(concepts) >= 20

    def test_morphology_nouns_loads(self) -> None:
        grammar = load_grammar_file(GREEK_GRAMMAR_DIR / "morphology" / "nouns.yml")
        assert grammar.language == "greek"
        assert grammar.category == "morphology"
        assert len(grammar.concepts) >= 5

    def test_morphology_verbs_loads(self) -> None:
        grammar = load_grammar_file(GREEK_GRAMMAR_DIR / "morphology" / "verbs.yml")
        assert grammar.language == "greek"
        assert grammar.category == "morphology"
        assert len(grammar.concepts) >= 10

    def test_morphology_adjectives_loads(self) -> None:
        grammar = load_grammar_file(GREEK_GRAMMAR_DIR / "morphology" / "adjectives.yml")
        assert grammar.language == "greek"
        assert len(grammar.concepts) >= 3

    def test_morphology_pronouns_loads(self) -> None:
        grammar = load_grammar_file(GREEK_GRAMMAR_DIR / "morphology" / "pronouns.yml")
        assert grammar.language == "greek"
        assert len(grammar.concepts) >= 4

    def test_morphology_participles_loads(self) -> None:
        grammar = load_grammar_file(
            GREEK_GRAMMAR_DIR / "morphology" / "participles.yml"
        )
        assert grammar.language == "greek"
        assert len(grammar.concepts) >= 5

    def test_syntax_cases_loads(self) -> None:
        grammar = load_grammar_file(GREEK_GRAMMAR_DIR / "syntax" / "cases.yml")
        assert grammar.language == "greek"
        assert grammar.category == "syntax"
        assert len(grammar.concepts) >= 5

    def test_syntax_particles_loads(self) -> None:
        grammar = load_grammar_file(GREEK_GRAMMAR_DIR / "syntax" / "particles.yml")
        assert grammar.language == "greek"
        assert len(grammar.concepts) >= 3

    def test_syntax_subordination_loads(self) -> None:
        grammar = load_grammar_file(GREEK_GRAMMAR_DIR / "syntax" / "subordination.yml")
        assert grammar.language == "greek"
        assert len(grammar.concepts) >= 4

    def test_syntax_indirect_discourse_loads(self) -> None:
        grammar = load_grammar_file(
            GREEK_GRAMMAR_DIR / "syntax" / "indirect-discourse.yml"
        )
        assert grammar.language == "greek"
        assert len(grammar.concepts) >= 3


@pytest.mark.unit
class TestGrammarFieldCompleteness:
    """Every grammar concept has all required fields."""

    @pytest.fixture(scope="class")
    def all_concepts(self) -> list[GrammarConceptData]:
        concepts, _ = load_all_grammar(CURRICULUM_PATH, "greek")
        return concepts

    def test_all_concepts_have_required_fields(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
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
        for c in all_concepts:
            assert c.examples and len(c.examples) >= 1, (
                f"concept {c.name} has no examples"
            )
            for ex in c.examples:
                assert ex.greek or ex.latin, (
                    f"concept {c.name} example missing greek/latin text"
                )
                assert ex.english, (
                    f"concept {c.name} example missing english translation"
                )

    def test_no_duplicate_concept_names(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
        names: set[str] = set()
        for c in all_concepts:
            assert c.name not in names, f"duplicate concept name: {c.name}"
            names.add(c.name)


@pytest.mark.unit
class TestPrerequisiteIntegrity:
    """Prerequisite references are valid and acyclic."""

    @pytest.fixture(scope="class")
    def all_concepts(self) -> list[GrammarConceptData]:
        concepts, _ = load_all_grammar(CURRICULUM_PATH, "greek")
        return concepts

    def test_prerequisites_resolve(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
        names = {c.name for c in all_concepts}
        for c in all_concepts:
            for prereq in c.prerequisites:
                assert prereq in names, (
                    f"concept {c.name} has unresolved prereq: {prereq}"
                )

    def test_dag_is_acyclic(self, all_concepts: list[GrammarConceptData]) -> None:
        assert len(all_concepts) > 0

    def test_difficulty_nondecreasing_along_prereqs(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
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
        concepts, _ = load_all_grammar(CURRICULUM_PATH, "greek")
        return concepts

    def test_sequence_loads(self) -> None:
        seq = load_grammar_sequence(GREEK_GRAMMAR_DIR / "sequence.yml")
        assert seq.language == "greek"
        assert len(seq.sequence) >= 2

    def test_sequence_references_valid_concepts(
        self, all_concepts: list[GrammarConceptData]
    ) -> None:
        seq = load_grammar_sequence(GREEK_GRAMMAR_DIR / "sequence.yml")
        defined_names = {c.name for c in all_concepts}
        for unit in seq.sequence:
            for concept_name in unit.concepts:
                assert concept_name in defined_names, (
                    f"sequence unit {unit.unit} references undefined "
                    f"concept: {concept_name}"
                )

    def test_sequence_units_ordered(self) -> None:
        seq = load_grammar_sequence(GREEK_GRAMMAR_DIR / "sequence.yml")
        unit_names = [u.unit for u in seq.sequence]
        assert unit_names == sorted(unit_names), (
            f"sequence units not in order: {unit_names}"
        )
