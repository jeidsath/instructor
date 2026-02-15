"""Lemmatization: find possible lemmas for a given word form.

Uses vocabulary form tables from the curriculum.  Given a set of
known vocabulary items with their paradigms, looks up which lemmas
could produce a given inflected form.
"""

from __future__ import annotations

from typing import Any

from instructor.nlp.morphology import _normalize, flatten_forms


def lemmatize(
    word: str,
    vocabulary: list[tuple[str, dict[str, Any] | None]],
) -> list[str]:
    """Return possible lemmas for *word*.

    Parameters
    ----------
    word:
        The inflected form to look up.
    vocabulary:
        A list of ``(lemma, forms_table)`` pairs representing known
        vocabulary.  The forms_table may be ``None`` for items with
        no paradigm data.

    Returns
    -------
    list[str]
        Unique lemmas whose paradigm includes *word*, ordered by
        first occurrence.
    """
    norm_word = _normalize(word)
    if not norm_word:
        return []

    seen: set[str] = set()
    results: list[str] = []

    for lemma, forms_table in vocabulary:
        if _normalize(lemma) == norm_word:
            if lemma not in seen:
                seen.add(lemma)
                results.append(lemma)
            continue

        for form_str, _ in flatten_forms(forms_table):
            if _normalize(form_str) == norm_word:
                if lemma not in seen:
                    seen.add(lemma)
                    results.append(lemma)
                break  # found a match for this lemma, move on

    return results
