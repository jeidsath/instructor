from pathlib import Path

import pytest
import yaml

from instructor.curriculum.loader import (
    CurriculumLoadError,
    load_grammar_file,
    load_vocabulary_set,
    validate_grammar_prerequisites,
)
from instructor.curriculum.registry import CurriculumRegistry
from instructor.curriculum.schemas import GrammarConceptData


@pytest.fixture
def tmp_curriculum(tmp_path: Path) -> Path:
    """Create a temporary curriculum directory with valid seed data."""
    latin_vocab = tmp_path / "latin" / "vocabulary"
    latin_vocab.mkdir(parents=True)

    latin_grammar = tmp_path / "latin" / "grammar" / "morphology"
    latin_grammar.mkdir(parents=True)

    # Valid vocabulary set
    vocab_data = {
        "language": "latin",
        "set": "test-001",
        "name": "Test Vocabulary",
        "items": [
            {
                "lemma": "sum",
                "pos": "verb",
                "definition": "to be",
                "difficulty": 1,
                "frequency_rank": 1,
            },
            {
                "lemma": "et",
                "pos": "conjunction",
                "definition": "and",
                "difficulty": 1,
                "frequency_rank": 2,
            },
        ],
    }
    with open(latin_vocab / "test-001.yml", "w") as f:
        yaml.dump(vocab_data, f)

    # Valid grammar file
    grammar_data = {
        "language": "latin",
        "category": "morphology",
        "concepts": [
            {
                "name": "First Declension",
                "subcategory": "noun_declension",
                "difficulty": 1,
                "prerequisites": [],
                "description": "First declension nouns.",
            },
            {
                "name": "Second Declension",
                "subcategory": "noun_declension",
                "difficulty": 2,
                "prerequisites": ["First Declension"],
                "description": "Second declension nouns.",
            },
        ],
    }
    with open(latin_grammar / "nouns.yml", "w") as f:
        yaml.dump(grammar_data, f)

    # Valid sequence
    sequence_data = {
        "language": "latin",
        "sequence": [
            {
                "unit": "01-foundations",
                "concepts": ["First Declension", "Second Declension"],
                "vocabulary_sets": ["test-001"],
            },
        ],
    }
    with open(tmp_path / "latin" / "grammar" / "sequence.yml", "w") as f:
        yaml.dump(sequence_data, f)

    return tmp_path


@pytest.mark.unit
def test_valid_vocabulary_loads(tmp_curriculum: Path) -> None:
    """Valid YAML loads and parses into correct dataclass."""
    path = tmp_curriculum / "latin" / "vocabulary" / "test-001.yml"
    vocab_set = load_vocabulary_set(path)
    assert vocab_set.language == "latin"
    assert vocab_set.set == "test-001"
    assert len(vocab_set.items) == 2
    assert vocab_set.items[0].lemma == "sum"
    assert vocab_set.items[0].pos == "verb"


@pytest.mark.unit
def test_malformed_yaml_raises_error(tmp_path: Path) -> None:
    """Malformed YAML raises clear error with file path."""
    bad_file = tmp_path / "bad.yml"
    bad_file.write_text("{{invalid yaml: [")
    with pytest.raises(CurriculumLoadError, match="invalid YAML"):
        load_vocabulary_set(bad_file)


@pytest.mark.unit
def test_missing_required_field(tmp_path: Path) -> None:
    """Missing required fields rejected with specific error."""
    data = {"language": "latin", "set": "x", "name": "x", "items": [
        {"lemma": "sum", "pos": "verb"}  # missing definition, difficulty
    ]}
    path = tmp_path / "missing.yml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    with pytest.raises(CurriculumLoadError):
        load_vocabulary_set(path)


@pytest.mark.unit
def test_missing_prerequisite_rejected() -> None:
    """Missing prerequisite reference rejected."""
    concepts = [
        GrammarConceptData(
            name="A",
            subcategory="test",
            difficulty=1,
            prerequisites=["NonExistent"],
            description="test",
        ),
    ]
    with pytest.raises(
        CurriculumLoadError, match="unresolved prerequisite.*NonExistent"
    ):
        validate_grammar_prerequisites(concepts)


@pytest.mark.unit
def test_circular_prerequisite_rejected() -> None:
    """Circular prerequisite dependency detected and rejected."""
    concepts = [
        GrammarConceptData(
            name="A",
            subcategory="test",
            difficulty=1,
            prerequisites=["B"],
            description="test",
        ),
        GrammarConceptData(
            name="B",
            subcategory="test",
            difficulty=1,
            prerequisites=["A"],
            description="test",
        ),
    ]
    with pytest.raises(
        CurriculumLoadError, match="circular prerequisite"
    ):
        validate_grammar_prerequisites(concepts)


@pytest.mark.unit
def test_difficulty_out_of_range(tmp_path: Path) -> None:
    """Difficulty level out of range rejected."""
    data = {
        "language": "latin",
        "set": "x",
        "name": "x",
        "items": [
            {
                "lemma": "sum",
                "pos": "verb",
                "definition": "to be",
                "difficulty": 15,
            },
        ],
    }
    path = tmp_path / "bad_diff.yml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    with pytest.raises(CurriculumLoadError):
        load_vocabulary_set(path)


@pytest.mark.unit
def test_duplicate_lemma_rejected(tmp_path: Path) -> None:
    """Duplicate vocabulary lemma within a set rejected."""
    data = {
        "language": "latin",
        "set": "x",
        "name": "x",
        "items": [
            {
                "lemma": "sum",
                "pos": "verb",
                "definition": "to be",
                "difficulty": 1,
            },
            {
                "lemma": "sum",
                "pos": "verb",
                "definition": "to be (dup)",
                "difficulty": 1,
            },
        ],
    }
    path = tmp_path / "dup.yml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    with pytest.raises(CurriculumLoadError, match="duplicate lemma"):
        load_vocabulary_set(path)


@pytest.mark.unit
def test_empty_vocabulary_set(tmp_path: Path) -> None:
    """Empty vocabulary set handled gracefully."""
    data = {
        "language": "latin",
        "set": "empty",
        "name": "Empty Set",
        "items": [],
    }
    path = tmp_path / "empty.yml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    vocab_set = load_vocabulary_set(path)
    assert len(vocab_set.items) == 0


@pytest.mark.unit
def test_invalid_pos_rejected(tmp_path: Path) -> None:
    """Invalid part of speech rejected."""
    data = {
        "language": "latin",
        "set": "x",
        "name": "x",
        "items": [
            {
                "lemma": "sum",
                "pos": "notapos",
                "definition": "to be",
                "difficulty": 1,
            },
        ],
    }
    path = tmp_path / "bad_pos.yml"
    with open(path, "w") as f:
        yaml.dump(data, f)
    with pytest.raises(CurriculumLoadError):
        load_vocabulary_set(path)


@pytest.mark.unit
def test_valid_grammar_loads(tmp_curriculum: Path) -> None:
    """Valid grammar YAML loads correctly."""
    path = (
        tmp_curriculum / "latin" / "grammar" / "morphology" / "nouns.yml"
    )
    grammar = load_grammar_file(path)
    assert grammar.language == "latin"
    assert grammar.category == "morphology"
    assert len(grammar.concepts) == 2
    assert grammar.concepts[0].name == "First Declension"
    assert grammar.concepts[1].prerequisites == ["First Declension"]


@pytest.mark.unit
def test_registry_loads_and_filters(tmp_curriculum: Path) -> None:
    """Registry methods return correct data filtered by language."""
    registry = CurriculumRegistry(tmp_curriculum)

    vocab_sets = registry.get_vocabulary_sets("latin")
    assert len(vocab_sets) == 1
    assert vocab_sets[0].set == "test-001"

    concepts = registry.get_grammar_concepts("latin")
    assert len(concepts) == 2

    sequence = registry.get_grammar_sequence("latin")
    assert sequence is not None
    assert len(sequence.sequence) == 1

    # Greek should be empty
    assert registry.get_vocabulary_sets("greek") == []
    assert registry.get_grammar_concepts("greek") == []


@pytest.mark.unit
def test_registry_with_real_seed_data() -> None:
    """Registry loads the actual seed curriculum data."""
    registry = CurriculumRegistry(Path("curriculum"))

    vocab_sets = registry.get_vocabulary_sets("latin")
    assert len(vocab_sets) >= 1
    assert vocab_sets[0].set == "core-001"
    assert len(vocab_sets[0].items) == 100

    concepts = registry.get_grammar_concepts("latin")
    assert len(concepts) >= 3

    sequence = registry.get_grammar_sequence("latin")
    assert sequence is not None
