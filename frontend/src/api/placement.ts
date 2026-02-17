import { apiFetch } from "./client";
import type {
  Language,
  PlacementResponseItem,
  PlacementResultResponse,
} from "./types";

export function submitPlacement(
  learnerId: string,
  language: Language,
  responses: PlacementResponseItem[],
): Promise<PlacementResultResponse> {
  return apiFetch<PlacementResultResponse>("/placement", {
    method: "POST",
    body: JSON.stringify({ learner_id: learnerId, language, responses }),
  });
}
