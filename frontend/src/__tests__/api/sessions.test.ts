import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  startSession,
  getNextActivity,
  submitResponse,
  endSession,
} from "../../api/sessions";

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

describe("sessions API", () => {
  it("startSession posts to /api/sessions", async () => {
    const session = {
      id: "s1",
      session_type: "practice",
      started_at: "2026-02-16T00:00:00Z",
      ended_at: null,
    };
    mockFetch.mockResolvedValue(jsonResponse(session, 201));

    const result = await startSession("abc", "greek");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/sessions",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ learner_id: "abc", language: "greek" }),
      }),
    );
    expect(result.id).toBe("s1");
  });

  it("getNextActivity fetches /api/sessions/:id/next", async () => {
    const activity = {
      index: 0,
      exercise_type: "definition_recall",
      prompt: "What does logos mean?",
      options: ["word", "fire", "water"],
    };
    mockFetch.mockResolvedValue(jsonResponse(activity));

    const result = await getNextActivity("s1");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/sessions/s1/next",
      expect.anything(),
    );
    expect(result.prompt).toBe("What does logos mean?");
  });

  it("submitResponse posts to /api/sessions/:id/submit", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ score: 1.0, correct: true, feedback: "Correct!" }),
    );

    const result = await submitResponse("s1", "word", 1500);

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/sessions/s1/submit",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ response: "word", time_taken_ms: 1500 }),
      }),
    );
    expect(result.correct).toBe(true);
  });

  it("endSession posts to /api/sessions/:id/end", async () => {
    const summary = {
      total_activities: 10,
      correct_count: 8,
      incorrect_count: 2,
      accuracy: 0.8,
    };
    mockFetch.mockResolvedValue(jsonResponse(summary));

    const result = await endSession("s1");

    expect(mockFetch).toHaveBeenCalledWith(
      "/api/sessions/s1/end",
      expect.objectContaining({ method: "POST" }),
    );
    expect(result.accuracy).toBe(0.8);
  });
});
