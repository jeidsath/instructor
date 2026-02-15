import pytest

from instructor.practice.exercises import (
    GeneratedExercise,
    generate_definition_recall,
    generate_definition_recognition,
    generate_fill_blank,
    generate_form_identification,
    generate_form_production,
    generate_translation,
    select_distractors,
)


@pytest.mark.unit
class TestDefinitionRecall:
    """generate_definition_recall creates correct exercise."""

    def test_basic(self) -> None:
        ex = generate_definition_recall(
            lemma="amō", definition="to love", language="Latin"
        )
        assert ex.exercise_type == "definition_recall"
        assert "amō" in ex.prompt
        assert ex.expected_response == "to love"

    def test_metadata(self) -> None:
        ex = generate_definition_recall(
            lemma="amō", definition="to love", language="Latin"
        )
        assert ex.metadata["lemma"] == "amō"
        assert ex.metadata["language"] == "Latin"


@pytest.mark.unit
class TestDefinitionRecognition:
    """generate_definition_recognition creates multiple-choice exercise."""

    def test_has_correct_answer(self) -> None:
        ex = generate_definition_recognition(
            lemma="amō",
            definition="to love",
            distractors=["to fear", "to run", "to eat"],
            language="Latin",
        )
        assert ex.expected_response == "to love"
        assert "to love" in ex.options

    def test_has_all_options(self) -> None:
        ex = generate_definition_recognition(
            lemma="amō",
            definition="to love",
            distractors=["to fear", "to run", "to eat"],
            language="Latin",
        )
        assert len(ex.options) == 4

    def test_options_shuffled(self) -> None:
        """Options should be shuffled (test multiple times for randomness)."""
        positions = set()
        for _ in range(20):
            ex = generate_definition_recognition(
                lemma="amō",
                definition="to love",
                distractors=["to fear", "to run", "to eat"],
                language="Latin",
            )
            positions.add(ex.options.index("to love"))
        # With 20 trials and 4 positions, should see >1 position
        assert len(positions) > 1


@pytest.mark.unit
class TestFormProduction:
    """generate_form_production creates form drill."""

    def test_basic(self) -> None:
        ex = generate_form_production(
            lemma="amō",
            target_features={"category": "present_active_indicative", "slot": "3s"},
            expected_form="amat",
            language="Latin",
        )
        assert ex.exercise_type == "form_production"
        assert ex.expected_response == "amat"
        assert "amō" in ex.prompt

    def test_features_in_prompt(self) -> None:
        ex = generate_form_production(
            lemma="amō",
            target_features={"category": "present_active_indicative", "slot": "3s"},
            expected_form="amat",
            language="Latin",
        )
        assert "present_active_indicative" in ex.prompt


@pytest.mark.unit
class TestFormIdentification:
    """generate_form_identification creates parse exercise."""

    def test_basic(self) -> None:
        ex = generate_form_identification(
            form="amat",
            lemma="amō",
            expected_parse={"category": "present_active_indicative", "slot": "3s"},
            language="Latin",
        )
        assert ex.exercise_type == "form_identification"
        assert "amat" in ex.prompt
        assert ex.metadata["expected_parse"]["slot"] == "3s"


@pytest.mark.unit
class TestFillBlank:
    """generate_fill_blank creates fill-in-the-blank exercise."""

    def test_basic(self) -> None:
        ex = generate_fill_blank(
            sentence_with_blank="Puella ___ videt.",
            expected_form="rosam",
            language="Latin",
        )
        assert ex.exercise_type == "fill_blank"
        assert "___" in ex.prompt
        assert ex.expected_response == "rosam"

    def test_with_hint(self) -> None:
        ex = generate_fill_blank(
            sentence_with_blank="Puella ___ videt.",
            expected_form="rosam",
            hint="rosa, accusative singular",
            language="Latin",
        )
        assert "Hint" in ex.prompt


@pytest.mark.unit
class TestTranslation:
    """generate_translation creates translation exercise."""

    def test_basic(self) -> None:
        ex = generate_translation(
            source_text="Amor vincit omnia.",
            direction="Latin to English",
            language="Latin",
        )
        assert ex.exercise_type == "translation"
        assert "Amor vincit omnia" in ex.prompt
        assert ex.expected_response == ""  # AI-scored

    def test_direction_in_prompt(self) -> None:
        ex = generate_translation(
            source_text="Hello",
            direction="English to Latin",
            language="Latin",
        )
        assert "English to Latin" in ex.prompt


@pytest.mark.unit
class TestSelectDistractors:
    """select_distractors picks incorrect options."""

    def test_excludes_correct(self) -> None:
        distractors = select_distractors(
            correct_definition="to love",
            all_definitions=["to love", "to fear", "to run", "to eat", "to see"],
        )
        assert "to love" not in distractors

    def test_correct_count(self) -> None:
        distractors = select_distractors(
            correct_definition="to love",
            all_definitions=["to love", "to fear", "to run", "to eat", "to see"],
            count=3,
        )
        assert len(distractors) == 3

    def test_fewer_than_requested(self) -> None:
        distractors = select_distractors(
            correct_definition="to love",
            all_definitions=["to love", "to fear"],
            count=3,
        )
        assert len(distractors) == 1  # only 1 candidate

    def test_empty_pool(self) -> None:
        distractors = select_distractors(
            correct_definition="to love",
            all_definitions=["to love"],
        )
        assert distractors == []


@pytest.mark.unit
class TestGeneratedExercise:
    """GeneratedExercise dataclass defaults."""

    def test_defaults(self) -> None:
        ex = GeneratedExercise(
            exercise_type="test",
            prompt="test",
            expected_response="test",
        )
        assert ex.options == []
        assert ex.metadata == {}
