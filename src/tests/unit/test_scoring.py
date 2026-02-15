import pytest

from instructor.evaluator.scoring import (
    ScoreResult,
    score_exact_match,
    score_fill_blank,
    score_form_match,
    score_parsing,
    score_synonym_match,
)


@pytest.mark.unit
class TestScoreResult:
    """ScoreResult invariants."""

    def test_score_clamped_to_range(self) -> None:
        r = ScoreResult(score=0.5, correct=True, feedback="ok", expected="x")
        assert 0.0 <= r.score <= 1.0

    def test_correct_true_when_perfect(self) -> None:
        r = ScoreResult(score=1.0, correct=True, feedback="ok", expected="x")
        assert r.correct is True

    def test_correct_false_when_wrong(self) -> None:
        r = ScoreResult(score=0.0, correct=False, feedback="no", expected="x")
        assert r.correct is False


@pytest.mark.unit
class TestExactMatch:
    """score_exact_match: case-insensitive, whitespace-normalized."""

    def test_exact_match(self) -> None:
        r = score_exact_match("amor", "amor")
        assert r.correct is True
        assert r.score == 1.0

    def test_case_insensitive(self) -> None:
        r = score_exact_match("AMOR", "amor")
        assert r.correct is True

    def test_whitespace_normalized(self) -> None:
        r = score_exact_match("  amor  ", "amor")
        assert r.correct is True

    def test_internal_whitespace_normalized(self) -> None:
        r = score_exact_match("to   love", "to love")
        assert r.correct is True

    def test_incorrect(self) -> None:
        r = score_exact_match("timor", "amor")
        assert r.correct is False
        assert r.score == 0.0

    def test_empty_response(self) -> None:
        r = score_exact_match("", "amor")
        assert r.correct is False
        assert r.score == 0.0

    def test_whitespace_only_response(self) -> None:
        r = score_exact_match("   ", "amor")
        assert r.correct is False

    def test_expected_in_result(self) -> None:
        r = score_exact_match("timor", "amor")
        assert r.expected == "amor"

    def test_feedback_on_correct(self) -> None:
        r = score_exact_match("amor", "amor")
        assert len(r.feedback) > 0

    def test_feedback_on_incorrect(self) -> None:
        r = score_exact_match("timor", "amor")
        assert len(r.feedback) > 0

    def test_macron_insensitive(self) -> None:
        r = score_exact_match("amō", "amo")
        assert r.correct is True

    def test_accent_insensitive(self) -> None:
        """Greek accents should not affect matching."""
        r = score_exact_match("λόγος", "λογος")
        assert r.correct is True

    def test_breathing_mark_insensitive(self) -> None:
        """Greek breathing marks should not affect matching."""
        r = score_exact_match("ἄνθρωπος", "ανθρωπος")
        assert r.correct is True

    def test_diacritics_both_present(self) -> None:
        """Matching works when both sides have diacritics."""
        r = score_exact_match("amō", "amō")
        assert r.correct is True


@pytest.mark.unit
class TestFormMatch:
    """score_form_match: accepts any valid form of the lemma."""

    def test_lemma_matches(self) -> None:
        r = score_form_match("amō", expected_lemma="amō", valid_forms=["amō", "amās"])
        assert r.correct is True
        assert r.score == 1.0

    def test_inflected_form_matches(self) -> None:
        r = score_form_match(
            "amās", expected_lemma="amō", valid_forms=["amō", "amās", "amat"]
        )
        assert r.correct is True

    def test_invalid_form_rejected(self) -> None:
        r = score_form_match(
            "timeo", expected_lemma="amō", valid_forms=["amō", "amās", "amat"]
        )
        assert r.correct is False

    def test_case_insensitive(self) -> None:
        r = score_form_match("AMOR", expected_lemma="amor", valid_forms=["amor"])
        assert r.correct is True

    def test_diacritic_insensitive(self) -> None:
        r = score_form_match("amo", expected_lemma="amō", valid_forms=["amō", "amās"])
        assert r.correct is True

    def test_empty_response(self) -> None:
        r = score_form_match("", expected_lemma="amō", valid_forms=["amō"])
        assert r.correct is False

    def test_empty_forms_list(self) -> None:
        r = score_form_match("amō", expected_lemma="amō", valid_forms=[])
        assert r.correct is False

    def test_expected_shows_lemma(self) -> None:
        r = score_form_match("bad", expected_lemma="amō", valid_forms=["amō"])
        assert r.expected == "amō"


@pytest.mark.unit
class TestSynonymMatch:
    """score_synonym_match: accepts known synonyms."""

    def test_exact_match(self) -> None:
        r = score_synonym_match("love", expected="love", synonyms=["affection"])
        assert r.correct is True

    def test_synonym_accepted(self) -> None:
        r = score_synonym_match(
            "affection", expected="love", synonyms=["affection", "fondness"]
        )
        assert r.correct is True

    def test_non_synonym_rejected(self) -> None:
        r = score_synonym_match("hate", expected="love", synonyms=["affection"])
        assert r.correct is False

    def test_case_insensitive(self) -> None:
        r = score_synonym_match("LOVE", expected="love", synonyms=[])
        assert r.correct is True

    def test_synonym_case_insensitive(self) -> None:
        r = score_synonym_match("Affection", expected="love", synonyms=["affection"])
        assert r.correct is True

    def test_empty_response(self) -> None:
        r = score_synonym_match("", expected="love", synonyms=["affection"])
        assert r.correct is False

    def test_empty_synonyms_list(self) -> None:
        r = score_synonym_match("love", expected="love", synonyms=[])
        assert r.correct is True

    def test_partial_match_rejected(self) -> None:
        r = score_synonym_match("lov", expected="love", synonyms=[])
        assert r.correct is False


@pytest.mark.unit
class TestParsing:
    """score_parsing: partial credit for multi-field answers."""

    def test_all_correct(self) -> None:
        r = score_parsing(
            {"case": "nominative", "number": "singular", "gender": "masculine"},
            {"case": "nominative", "number": "singular", "gender": "masculine"},
        )
        assert r.correct is True
        assert r.score == 1.0

    def test_partial_credit(self) -> None:
        r = score_parsing(
            {"case": "nominative", "number": "singular", "gender": "feminine"},
            {"case": "nominative", "number": "singular", "gender": "masculine"},
        )
        assert r.correct is False
        assert r.score == pytest.approx(2 / 3)

    def test_all_wrong(self) -> None:
        r = score_parsing(
            {"case": "genitive", "number": "plural", "gender": "neuter"},
            {"case": "nominative", "number": "singular", "gender": "masculine"},
        )
        assert r.correct is False
        assert r.score == 0.0

    def test_missing_field_in_response(self) -> None:
        r = score_parsing(
            {"case": "nominative"},
            {"case": "nominative", "number": "singular", "gender": "masculine"},
        )
        assert r.score == pytest.approx(1 / 3)

    def test_extra_field_in_response_ignored(self) -> None:
        """Extra fields in response don't affect score; only expected fields count."""
        r = score_parsing(
            {"case": "nominative", "extra": "value"},
            {"case": "nominative"},
        )
        assert r.correct is True
        assert r.score == 1.0

    def test_case_insensitive(self) -> None:
        r = score_parsing(
            {"case": "NOMINATIVE"},
            {"case": "nominative"},
        )
        assert r.correct is True

    def test_empty_response(self) -> None:
        r = score_parsing(
            {},
            {"case": "nominative", "number": "singular"},
        )
        assert r.score == 0.0

    def test_single_field(self) -> None:
        r = score_parsing(
            {"case": "nominative"},
            {"case": "nominative"},
        )
        assert r.correct is True
        assert r.score == 1.0

    def test_feedback_lists_wrong_fields(self) -> None:
        r = score_parsing(
            {"case": "genitive", "number": "singular"},
            {"case": "nominative", "number": "singular"},
        )
        assert "case" in r.feedback


@pytest.mark.unit
class TestFillBlank:
    """score_fill_blank: form matching with morphological flexibility."""

    def test_exact_match(self) -> None:
        r = score_fill_blank("amāt", expected_form="amāt", valid_forms=["amāt"])
        assert r.correct is True

    def test_alternative_form_accepted(self) -> None:
        r = score_fill_blank("amat", expected_form="amāt", valid_forms=["amāt", "amat"])
        assert r.correct is True

    def test_wrong_form(self) -> None:
        r = score_fill_blank("amō", expected_form="amāt", valid_forms=["amāt", "amat"])
        assert r.correct is False

    def test_diacritic_insensitive(self) -> None:
        r = score_fill_blank("amat", expected_form="amāt", valid_forms=["amāt"])
        assert r.correct is True

    def test_empty_response(self) -> None:
        r = score_fill_blank("", expected_form="amāt", valid_forms=["amāt"])
        assert r.correct is False

    def test_expected_in_result(self) -> None:
        r = score_fill_blank("wrong", expected_form="amāt", valid_forms=["amāt"])
        assert r.expected == "amāt"
