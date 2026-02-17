import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router";
import { LearnerContext } from "../context/learner-context";
import type { LearnerContextValue } from "../context/learner-context";
import PracticeSessionPage from "../pages/PracticeSessionPage";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const mockCtx: LearnerContextValue = {
  learner: { id: "abc", name: "Alice" },
  setLearner: vi.fn(),
  clearLearner: vi.fn(),
};

function renderPage(ctx = mockCtx) {
  return render(
    <MemoryRouter initialEntries={["/practice/latin"]}>
      <LearnerContext value={ctx}>
        <Routes>
          <Route
            path="/practice/:language"
            element={<PracticeSessionPage />}
          />
        </Routes>
      </LearnerContext>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  mockFetch.mockReset();
});

describe("PracticeSessionPage", () => {
  it("shows starting state then exercise", async () => {
    let callNum = 0;
    mockFetch.mockImplementation(() => {
      callNum++;
      if (callNum === 1) {
        // POST /api/sessions
        return Promise.resolve(
          jsonResponse(
            {
              id: "s1",
              session_type: "practice",
              started_at: "2026-02-16T00:00:00Z",
              ended_at: null,
            },
            201,
          ),
        );
      }
      // GET /api/sessions/s1/next
      return Promise.resolve(
        jsonResponse({
          index: 0,
          exercise_type: "definition_recall",
          prompt: "What does 'amor' mean?",
          options: ["love", "war", "peace"],
        }),
      );
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("What does 'amor' mean?")).toBeInTheDocument();
    });
    expect(screen.getByText("love")).toBeInTheDocument();
    expect(screen.getByText("war")).toBeInTheDocument();
    expect(screen.getByText("peace")).toBeInTheDocument();
  });

  it("submits answer and shows feedback", async () => {
    let callNum = 0;
    mockFetch.mockImplementation(() => {
      callNum++;
      if (callNum === 1) {
        return Promise.resolve(
          jsonResponse({
            id: "s1",
            session_type: "practice",
            started_at: "2026-02-16T00:00:00Z",
            ended_at: null,
          }, 201),
        );
      }
      if (callNum === 2) {
        return Promise.resolve(
          jsonResponse({
            index: 0,
            exercise_type: "definition_recall",
            prompt: "What does 'amor' mean?",
            options: ["love", "war", "peace"],
          }),
        );
      }
      // POST /api/sessions/s1/submit
      return Promise.resolve(
        jsonResponse({ score: 1.0, correct: true, feedback: "Well done!" }),
      );
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("What does 'amor' mean?")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("love"));
    await userEvent.click(screen.getByRole("button", { name: /submit/i }));

    await waitFor(() => {
      expect(screen.getByText("Correct!")).toBeInTheDocument();
    });
    expect(screen.getByText("Well done!")).toBeInTheDocument();
  });

  it("shows session summary when no more exercises", async () => {
    let callNum = 0;
    mockFetch.mockImplementation(() => {
      callNum++;
      if (callNum === 1) {
        return Promise.resolve(
          jsonResponse({
            id: "s1",
            session_type: "practice",
            started_at: "2026-02-16T00:00:00Z",
            ended_at: null,
          }, 201),
        );
      }
      if (callNum === 2) {
        // GET /next returns 404 = session complete
        return Promise.resolve(
          jsonResponse({ detail: "Session is complete" }, 404),
        );
      }
      // POST /end
      return Promise.resolve(
        jsonResponse({
          total_activities: 10,
          correct_count: 8,
          incorrect_count: 2,
          accuracy: 0.8,
        }),
      );
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Session Complete")).toBeInTheDocument();
    });
    expect(screen.getByText("80%")).toBeInTheDocument();
  });

  it("shows error when session fails to start", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ detail: "Not found" }, 404),
    );

    renderPage();

    await waitFor(() => {
      expect(
        screen.getByText(/no learner state found/i),
      ).toBeInTheDocument();
    });
  });
});
