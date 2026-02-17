import { apiFetch } from "./client";
import type {
  GrammarConceptResponse,
  Language,
  VocabularySetResponse,
} from "./types";

export function getVocabularySets(
  language: Language,
): Promise<VocabularySetResponse[]> {
  return apiFetch<VocabularySetResponse[]>(
    `/curriculum/${language}/vocabulary`,
  );
}

export function getGrammarConcepts(
  language: Language,
): Promise<GrammarConceptResponse[]> {
  return apiFetch<GrammarConceptResponse[]>(
    `/curriculum/${language}/grammar`,
  );
}
