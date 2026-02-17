import { apiFetch } from "./client";
import type { Language, LearnerResponse, LearnerStateResponse } from "./types";

export function createLearner(name: string): Promise<LearnerResponse> {
  return apiFetch<LearnerResponse>("/learners", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function getLearner(id: string): Promise<LearnerResponse> {
  return apiFetch<LearnerResponse>(`/learners/${id}`);
}

export function getLearnerState(
  id: string,
  language: Language,
): Promise<LearnerStateResponse> {
  return apiFetch<LearnerStateResponse>(
    `/learners/${id}/state/${language}`,
  );
}
