import { describe, it, expect, vi, beforeEach } from "vitest";
import { createLearner, getLearner, getLearnerState } from "../../api/learners";

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

describe("learners API", () => {
  it("createLearner posts to /api/learners", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ id: "abc", name: "Alice" }, 201),
    );

    const result = await createLearner("Alice");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/learners",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ name: "Alice" }),
      }),
    );
    expect(result).toEqual({ id: "abc", name: "Alice" });
  });

  it("getLearner fetches /api/learners/:id", async () => {
    mockFetch.mockResolvedValue(jsonResponse({ id: "abc", name: "Alice" }));

    const result = await getLearner("abc");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/learners/abc",
      expect.anything(),
    );
    expect(result.name).toBe("Alice");
  });

  it("getLearnerState fetches /api/learners/:id/state/:language", async () => {
    const state = {
      language: "latin",
      reading_level: 3.0,
      writing_level: 2.0,
      listening_level: 1.0,
      speaking_level: 0.5,
      active_vocabulary_size: 100,
      grammar_concepts_mastered: 5,
      last_session_at: null,
      total_study_time_minutes: 120,
    };
    mockFetch.mockResolvedValue(jsonResponse(state));

    const result = await getLearnerState("abc", "latin");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/learners/abc/state/latin",
      expect.anything(),
    );
    expect(result.active_vocabulary_size).toBe(100);
  });
});
