import enum


class Language(enum.StrEnum):
    GREEK = "greek"
    LATIN = "latin"


class PartOfSpeech(enum.StrEnum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    PARTICLE = "particle"
    PRONOUN = "pronoun"
    INTERJECTION = "interjection"


class GrammarCategory(enum.StrEnum):
    MORPHOLOGY = "morphology"
    SYNTAX = "syntax"
    PHONOLOGY = "phonology"
    PROSODY = "prosody"


class MasteryLevel(int, enum.Enum):
    UNKNOWN = 0
    INTRODUCED = 1
    PRACTICING = 2
    FAMILIAR = 3
    PROFICIENT = 4
    MASTERED = 5


class SessionType(enum.StrEnum):
    LESSON = "lesson"
    PRACTICE = "practice"
    EVALUATION = "evaluation"
    PLACEMENT = "placement"
