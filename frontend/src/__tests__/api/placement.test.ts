import { describe, it, expect, vi, beforeEach } from "vitest";
import { submitPlacement } from "../../api/placement";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

beforeEach(() => {
  mockFetch.mockReset();
});

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("placement API", () => {
  it("submitPlacement posts to /api/placement", async () => {
    const result = {
      total_score: 0.6,
      vocabulary_score: 0.7,
      grammar_score: 0.5,
      reading_score: 0.6,
      starting_unit: 3,
    };
    mockFetch.mockResolvedValue(jsonResponse(result));

    const responses = [
      { probe_type: "vocabulary", difficulty: 1, correct: true, item_id: "v1" },
      { probe_type: "grammar", difficulty: 2, correct: false, item_id: "g1" },
    ];

    const res = await submitPlacement("abc", "greek", responses);

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/placement",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          learner_id: "abc",
          language: "greek",
          responses,
        }),
      }),
    );
    expect(res.starting_unit).toBe(3);
  });
});
