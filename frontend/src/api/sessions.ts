import { apiFetch } from "./client";
import type {
  ActivityResponse,
  ActivityResultResponse,
  Language,
  SessionResponse,
  SessionSummaryResponse,
} from "./types";

export function startSession(
  learnerId: string,
  language: Language,
): Promise<SessionResponse> {
  return apiFetch<SessionResponse>("/sessions", {
    method: "POST",
    body: JSON.stringify({ learner_id: learnerId, language }),
  });
}

export function getNextActivity(
  sessionId: string,
): Promise<ActivityResponse> {
  return apiFetch<ActivityResponse>(`/sessions/${sessionId}/next`);
}

export function submitResponse(
  sessionId: string,
  response: string,
  timeMs: number,
): Promise<ActivityResultResponse> {
  return apiFetch<ActivityResultResponse>(`/sessions/${sessionId}/submit`, {
    method: "POST",
    body: JSON.stringify({ response, time_taken_ms: timeMs }),
  });
}

export function endSession(
  sessionId: string,
): Promise<SessionSummaryResponse> {
  return apiFetch<SessionSummaryResponse>(`/sessions/${sessionId}/end`, {
    method: "POST",
  });
}
