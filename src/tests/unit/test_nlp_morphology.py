import pytest

from instructor.nlp.lemmatizer import lemmatize
from instructor.nlp.morphology import (
    analyze_form,
    extract_all_forms,
    flatten_forms,
    generate_form,
    is_valid_form_of,
)

# ------------------------------------------------------------------
# Sample paradigm tables
# ------------------------------------------------------------------

LATIN_VERB_FORMS = {
    "present_active_indicative": {
        "1s": "amō",
        "2s": "amās",
        "3s": "amat",
        "1p": "amāmus",
        "2p": "amātis",
        "3p": "amant",
    },
    "imperfect_active_indicative": {
        "1s": "amābam",
        "3s": "amābat",
    },
}

LATIN_NOUN_FORMS = {
    "nominative_singular": "rosa",
    "genitive_singular": "rosae",
    "dative_singular": "rosae",
    "accusative_singular": "rosam",
    "ablative_singular": "rosā",
    "nominative_plural": "rosae",
    "genitive_plural": "rosārum",
}

GREEK_VERB_FORMS = {
    "present_active_indicative": {
        "1s": "λύω",
        "2s": "λύεις",
        "3s": "λύει",
    },
}


# ------------------------------------------------------------------
# flatten_forms
# ------------------------------------------------------------------


@pytest.mark.unit
class TestFlattenForms:
    """flatten_forms handles nested and flat form tables."""

    def test_nested_table(self) -> None:
        result = flatten_forms(LATIN_VERB_FORMS)
        forms = [f for f, _ in result]
        assert "amō" in forms
        assert "amās" in forms

    def test_flat_table(self) -> None:
        result = flatten_forms(LATIN_NOUN_FORMS)
        forms = [f for f, _ in result]
        assert "rosa" in forms
        assert "rosam" in forms

    def test_none_returns_empty(self) -> None:
        assert flatten_forms(None) == []

    def test_empty_dict_returns_empty(self) -> None:
        assert flatten_forms({}) == []

    def test_features_for_nested(self) -> None:
        result = flatten_forms(LATIN_VERB_FORMS)
        for form_str, features in result:
            if form_str == "amās":
                assert features["category"] == "present_active_indicative"
                assert features["slot"] == "2s"
                return
        pytest.fail("amās not found")

    def test_features_for_flat(self) -> None:
        result = flatten_forms(LATIN_NOUN_FORMS)
        for form_str, features in result:
            if form_str == "rosam":
                assert features["slot"] == "accusative_singular"
                return
        pytest.fail("rosam not found")


# ------------------------------------------------------------------
# extract_all_forms
# ------------------------------------------------------------------


@pytest.mark.unit
class TestExtractAllForms:
    """extract_all_forms returns unique strings."""

    def test_returns_all_unique(self) -> None:
        forms = extract_all_forms(LATIN_VERB_FORMS)
        assert "amō" in forms
        assert "amat" in forms
        assert len(forms) == len(set(forms))

    def test_noun_forms(self) -> None:
        forms = extract_all_forms(LATIN_NOUN_FORMS)
        assert "rosa" in forms
        # rosae appears multiple times in table but should be unique
        assert forms.count("rosae") <= 1

    def test_none_returns_empty(self) -> None:
        assert extract_all_forms(None) == []


# ------------------------------------------------------------------
# is_valid_form_of
# ------------------------------------------------------------------


@pytest.mark.unit
class TestIsValidFormOf:
    """is_valid_form_of checks lemma and paradigm."""

    def test_lemma_matches(self) -> None:
        assert is_valid_form_of("amō", "amō", LATIN_VERB_FORMS) is True

    def test_inflected_form_matches(self) -> None:
        assert is_valid_form_of("amās", "amō", LATIN_VERB_FORMS) is True

    def test_case_insensitive(self) -> None:
        assert is_valid_form_of("ROSA", "rosa", LATIN_NOUN_FORMS) is True

    def test_diacritic_insensitive(self) -> None:
        assert is_valid_form_of("amo", "amō", LATIN_VERB_FORMS) is True

    def test_invalid_form(self) -> None:
        assert is_valid_form_of("timeo", "amō", LATIN_VERB_FORMS) is False

    def test_empty_form(self) -> None:
        assert is_valid_form_of("", "amō", LATIN_VERB_FORMS) is False

    def test_none_forms_table(self) -> None:
        # Lemma itself should still match
        assert is_valid_form_of("amō", "amō", None) is True

    def test_none_forms_table_non_lemma(self) -> None:
        assert is_valid_form_of("amās", "amō", None) is False

    def test_greek_form(self) -> None:
        assert is_valid_form_of("λύεις", "λύω", GREEK_VERB_FORMS) is True

    def test_greek_without_accents(self) -> None:
        assert is_valid_form_of("λυω", "λύω", GREEK_VERB_FORMS) is True


# ------------------------------------------------------------------
# analyze_form
# ------------------------------------------------------------------


@pytest.mark.unit
class TestAnalyzeForm:
    """analyze_form returns MorphologicalAnalysis objects."""

    def test_lemma_analyzed(self) -> None:
        results = analyze_form("amō", "amō", LATIN_VERB_FORMS)
        # Should match as both lemma and 1s present active
        lemma_matches = [r for r in results if r.features.get("slot") == "lemma"]
        assert len(lemma_matches) == 1

    def test_inflected_form_analyzed(self) -> None:
        results = analyze_form("amat", "amō", LATIN_VERB_FORMS)
        assert len(results) >= 1
        assert results[0].lemma == "amō"
        assert results[0].features["slot"] == "3s"

    def test_no_match_returns_empty(self) -> None:
        assert analyze_form("timeo", "amō", LATIN_VERB_FORMS) == []

    def test_empty_form_returns_empty(self) -> None:
        assert analyze_form("", "amō", LATIN_VERB_FORMS) == []

    def test_flat_table(self) -> None:
        results = analyze_form("rosam", "rosa", LATIN_NOUN_FORMS)
        assert len(results) == 1
        assert results[0].features["slot"] == "accusative_singular"

    def test_ambiguous_form(self) -> None:
        """rosae is both genitive_singular and dative_singular and nominative_plural."""
        results = analyze_form("rosae", "rosa", LATIN_NOUN_FORMS)
        assert len(results) >= 2  # at least gen sg and dat sg


# ------------------------------------------------------------------
# generate_form
# ------------------------------------------------------------------


@pytest.mark.unit
class TestGenerateForm:
    """generate_form produces inflected forms."""

    def test_nested_lookup(self) -> None:
        result = generate_form(
            "amō",
            {"category": "present_active_indicative", "slot": "3s"},
            LATIN_VERB_FORMS,
        )
        assert result == "amat"

    def test_flat_lookup(self) -> None:
        result = generate_form(
            "rosa",
            {"slot": "accusative_singular"},
            LATIN_NOUN_FORMS,
        )
        assert result == "rosam"

    def test_missing_category(self) -> None:
        result = generate_form(
            "amō",
            {"category": "future_active_indicative", "slot": "1s"},
            LATIN_VERB_FORMS,
        )
        assert result is None

    def test_missing_slot(self) -> None:
        result = generate_form(
            "amō",
            {"category": "present_active_indicative", "slot": "nonexistent"},
            LATIN_VERB_FORMS,
        )
        assert result is None

    def test_none_forms_table(self) -> None:
        assert generate_form("amō", {"slot": "1s"}, None) is None


# ------------------------------------------------------------------
# lemmatize
# ------------------------------------------------------------------


@pytest.mark.unit
class TestLemmatize:
    """lemmatize finds possible lemmas from vocabulary."""

    def test_finds_lemma_by_citation_form(self) -> None:
        vocab = [("amō", LATIN_VERB_FORMS), ("rosa", LATIN_NOUN_FORMS)]
        result = lemmatize("amō", vocab)
        assert result == ["amō"]

    def test_finds_lemma_by_inflected_form(self) -> None:
        vocab = [("amō", LATIN_VERB_FORMS), ("rosa", LATIN_NOUN_FORMS)]
        result = lemmatize("rosam", vocab)
        assert result == ["rosa"]

    def test_no_match(self) -> None:
        vocab = [("amō", LATIN_VERB_FORMS)]
        result = lemmatize("timeo", vocab)
        assert result == []

    def test_diacritic_insensitive(self) -> None:
        vocab = [("amō", LATIN_VERB_FORMS)]
        result = lemmatize("amo", vocab)
        assert result == ["amō"]

    def test_empty_word(self) -> None:
        vocab = [("amō", LATIN_VERB_FORMS)]
        assert lemmatize("", vocab) == []

    def test_empty_vocabulary(self) -> None:
        assert lemmatize("amō", []) == []

    def test_multiple_lemmas_possible(self) -> None:
        """If two lemmas have the same form, both should be returned."""
        # Both "sum" forms and a hypothetical other verb that has "est"
        forms_a = {"present": {"3s": "est"}}
        forms_b = {"present": {"3s": "est"}}
        vocab = [("sum", forms_a), ("edo", forms_b)]
        result = lemmatize("est", vocab)
        assert result == ["sum", "edo"]

    def test_no_duplicate_lemmas(self) -> None:
        """Lemma should appear at most once even if form and lemma match."""
        vocab = [("amō", LATIN_VERB_FORMS)]
        result = lemmatize("amō", vocab)
        assert result == ["amō"]

    def test_none_forms_table_matches_lemma(self) -> None:
        vocab = [("et", None)]
        result = lemmatize("et", vocab)
        assert result == ["et"]
