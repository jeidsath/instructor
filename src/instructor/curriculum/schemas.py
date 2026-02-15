from pydantic import BaseModel, field_validator


class VocabularyItemData(BaseModel):
    lemma: str
    pos: str
    definition: str
    frequency_rank: int | None = None
    difficulty: int
    forms: dict[str, object] | None = None
    notes: str | None = None

    @field_validator("difficulty")
    @classmethod
    def difficulty_in_range(cls, v: int) -> int:
        if not 1 <= v <= 10:
            msg = f"difficulty must be 1-10, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("pos")
    @classmethod
    def valid_pos(cls, v: str) -> str:
        valid = {
            "noun", "verb", "adjective", "adverb", "preposition",
            "conjunction", "particle", "pronoun", "interjection",
        }
        if v not in valid:
            msg = f"invalid part of speech: {v}"
            raise ValueError(msg)
        return v


class VocabularySetData(BaseModel):
    language: str
    set: str
    name: str
    description: str | None = None
    items: list[VocabularyItemData]

    @field_validator("language")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("greek", "latin"):
            msg = f"language must be 'greek' or 'latin', got '{v}'"
            raise ValueError(msg)
        return v


class GrammarExampleData(BaseModel):
    latin: str | None = None
    greek: str | None = None
    english: str
    notes: str | None = None


class GrammarConceptData(BaseModel):
    name: str
    subcategory: str
    difficulty: int
    prerequisites: list[str] = []
    description: str
    paradigm: dict[str, object] | None = None
    examples: list[GrammarExampleData] | None = None

    @field_validator("difficulty")
    @classmethod
    def difficulty_in_range(cls, v: int) -> int:
        if not 1 <= v <= 10:
            msg = f"difficulty must be 1-10, got {v}"
            raise ValueError(msg)
        return v


class GrammarFileData(BaseModel):
    language: str
    category: str
    concepts: list[GrammarConceptData]

    @field_validator("language")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("greek", "latin"):
            msg = f"language must be 'greek' or 'latin', got '{v}'"
            raise ValueError(msg)
        return v

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str) -> str:
        valid = {"morphology", "syntax", "phonology", "prosody"}
        if v not in valid:
            msg = f"invalid category: {v}"
            raise ValueError(msg)
        return v


class SequenceUnitData(BaseModel):
    unit: str
    concepts: list[str]
    vocabulary_sets: list[str] = []


class GrammarSequenceData(BaseModel):
    language: str
    sequence: list[SequenceUnitData]

    @field_validator("language")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("greek", "latin"):
            msg = f"language must be 'greek' or 'latin', got '{v}'"
            raise ValueError(msg)
        return v


class VocabularyNoteData(BaseModel):
    word: str
    note: str


class GrammarNoteData(BaseModel):
    concept: str
    note: str


class TextEntryData(BaseModel):
    language: str
    title: str
    author: str | None = None
    difficulty: int
    content: str
    translation: str | None = None
    vocabulary_notes: list[VocabularyNoteData] | None = None
    grammar_notes: list[GrammarNoteData] | None = None
    prerequisite_grammar: list[str] | None = None

    @field_validator("difficulty")
    @classmethod
    def difficulty_in_range(cls, v: int) -> int:
        if not 1 <= v <= 10:
            msg = f"difficulty must be 1-10, got {v}"
            raise ValueError(msg)
        return v

    @field_validator("language")
    @classmethod
    def valid_language(cls, v: str) -> str:
        if v not in ("greek", "latin"):
            msg = f"language must be 'greek' or 'latin', got '{v}'"
            raise ValueError(msg)
        return v
