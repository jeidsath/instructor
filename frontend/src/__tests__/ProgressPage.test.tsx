import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router";
import { LearnerContext } from "../context/learner-context";
import type { LearnerContextValue } from "../context/learner-context";
import ProgressPage from "../pages/ProgressPage";

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
    <MemoryRouter>
      <LearnerContext value={ctx}>
        <ProgressPage />
      </LearnerContext>
    </MemoryRouter>,
  );
}

const latinState = {
  language: "latin",
  reading_level: 3.2,
  writing_level: 2.0,
  listening_level: 1.5,
  speaking_level: 0.8,
  active_vocabulary_size: 124,
  grammar_concepts_mastered: 8,
  last_session_at: "2026-02-14T12:00:00Z",
  total_study_time_minutes: 270,
};

beforeEach(() => {
  mockFetch.mockReset();
});

describe("ProgressPage", () => {
  it("shows progress when one language has state", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/greek")) {
        return Promise.resolve(jsonResponse({ detail: "Not found" }, 404));
      }
      return Promise.resolve(jsonResponse(latinState));
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("124")).toBeInTheDocument();
    });
    expect(screen.getByText("Words learned")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
    expect(screen.getByText("Concepts mastered")).toBeInTheDocument();
    expect(screen.getByText("4 hours 30 minutes")).toBeInTheDocument();
  });

  it("shows no-progress message when both are 404", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ detail: "Not found" }, 404),
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/no progress yet/i)).toBeInTheDocument();
    });
  });

  it("shows skill bars with color coding", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/greek")) {
        return Promise.resolve(jsonResponse({ detail: "Not found" }, 404));
      }
      return Promise.resolve(jsonResponse(latinState));
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Reading")).toBeInTheDocument();
    });
    expect(screen.getByText("3.2")).toBeInTheDocument();
    expect(screen.getByText("Writing")).toBeInTheDocument();
    expect(screen.getByText("Listening")).toBeInTheDocument();
    expect(screen.getByText("Speaking")).toBeInTheDocument();
  });
});
