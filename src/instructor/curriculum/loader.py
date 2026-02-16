from pathlib import Path

import yaml
from pydantic import ValidationError

from instructor.curriculum.schemas import (
    GrammarConceptData,
    GrammarFileData,
    GrammarSequenceData,
    TextEntryData,
    VocabularySetData,
)


class CurriculumLoadError(Exception):
    """Raised when curriculum data fails validation."""

    def __init__(self, message: str, file_path: Path | None = None) -> None:
        self.file_path = file_path
        prefix = f"{file_path}: " if file_path else ""
        super().__init__(f"{prefix}{message}")


def load_yaml_file(path: Path) -> object:
    """Load and parse a YAML file."""
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise CurriculumLoadError(f"invalid YAML: {e}", path) from e


def load_vocabulary_set(path: Path) -> VocabularySetData:
    """Load and validate a vocabulary set YAML file."""
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise CurriculumLoadError("expected a YAML mapping", path)
    try:
        vocab_set = VocabularySetData(**data)
    except ValidationError as e:
        raise CurriculumLoadError(str(e), path) from e

    # Check for duplicate lemmas within the set
    seen: set[tuple[str, str]] = set()
    for item in vocab_set.items:
        key = (item.lemma, item.pos)
        if key in seen:
            raise CurriculumLoadError(
                f"duplicate lemma+pos: {item.lemma} ({item.pos})", path
            )
        seen.add(key)

    return vocab_set


def load_grammar_file(path: Path) -> GrammarFileData:
    """Load and validate a grammar concepts YAML file."""
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise CurriculumLoadError("expected a YAML mapping", path)
    try:
        return GrammarFileData(**data)
    except ValidationError as e:
        raise CurriculumLoadError(str(e), path) from e


def load_grammar_sequence(path: Path) -> GrammarSequenceData:
    """Load and validate a grammar sequence YAML file."""
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise CurriculumLoadError("expected a YAML mapping", path)
    try:
        return GrammarSequenceData(**data)
    except ValidationError as e:
        raise CurriculumLoadError(str(e), path) from e


def load_text_entry(path: Path) -> TextEntryData:
    """Load and validate a text entry YAML file."""
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise CurriculumLoadError("expected a YAML mapping", path)
    try:
        return TextEntryData(**data)
    except ValidationError as e:
        raise CurriculumLoadError(str(e), path) from e


def validate_grammar_prerequisites(
    concepts: list[GrammarConceptData],
    file_path: Path | None = None,
) -> None:
    """Validate that all prerequisite references resolve and there are no cycles."""
    names = {c.name for c in concepts}

    # Check all prerequisites reference existing concepts
    for concept in concepts:
        for prereq in concept.prerequisites:
            if prereq not in names:
                raise CurriculumLoadError(
                    f"concept '{concept.name}' has unresolved prerequisite: '{prereq}'",
                    file_path,
                )

    # Check for cycles using DFS
    prereq_map = {c.name: c.prerequisites for c in concepts}
    visited: set[str] = set()
    in_stack: set[str] = set()

    def dfs(name: str) -> None:
        if name in in_stack:
            raise CurriculumLoadError(
                f"circular prerequisite dependency involving '{name}'",
                file_path,
            )
        if name in visited:
            return
        in_stack.add(name)
        for prereq in prereq_map.get(name, []):
            dfs(prereq)
        in_stack.remove(name)
        visited.add(name)

    for concept in concepts:
        dfs(concept.name)


def load_all_vocabulary(base_path: Path, language: str) -> list[VocabularySetData]:
    """Load all vocabulary sets for a language."""
    vocab_dir = base_path / language / "vocabulary"
    if not vocab_dir.exists():
        return []
    results = []
    for path in sorted(vocab_dir.glob("*.yml")):
        vocab_set = load_vocabulary_set(path)
        if vocab_set.language != language:
            raise CurriculumLoadError(
                f"language mismatch: file is under '{language}/' "
                f"but declares language '{vocab_set.language}'",
                path,
            )
        results.append(vocab_set)
    return results


def load_all_grammar(
    base_path: Path, language: str
) -> tuple[list[GrammarConceptData], GrammarSequenceData | None]:
    """Load all grammar concepts and sequence for a language."""
    grammar_dir = base_path / language / "grammar"
    if not grammar_dir.exists():
        return [], None

    # Load all concept files
    all_concepts: list[GrammarConceptData] = []
    for path in sorted(grammar_dir.rglob("*.yml")):
        if path.name == "sequence.yml":
            continue
        grammar_file = load_grammar_file(path)
        if grammar_file.language != language:
            raise CurriculumLoadError(
                f"language mismatch: file is under '{language}/' "
                f"but declares language '{grammar_file.language}'",
                path,
            )
        for concept in grammar_file.concepts:
            concept.category = grammar_file.category
        all_concepts.extend(grammar_file.concepts)

    # Validate prerequisites across all concepts
    if all_concepts:
        validate_grammar_prerequisites(all_concepts)

    # Load sequence if it exists
    sequence_path = grammar_dir / "sequence.yml"
    sequence = None
    if sequence_path.exists():
        sequence = load_grammar_sequence(sequence_path)

    return all_concepts, sequence


def load_all_texts(base_path: Path, language: str) -> list[TextEntryData]:
    """Load all text entries for a language."""
    texts_dir = base_path / language / "texts"
    if not texts_dir.exists():
        return []
    results = []
    for path in sorted(texts_dir.rglob("*.yml")):
        text_entry = load_text_entry(path)
        if text_entry.language != language:
            raise CurriculumLoadError(
                f"language mismatch: file is under '{language}/' "
                f"but declares language '{text_entry.language}'",
                path,
            )
        results.append(text_entry)
    return results
