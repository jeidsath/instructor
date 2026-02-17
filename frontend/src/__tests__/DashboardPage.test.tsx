import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter } from "react-router";
import { LearnerContext } from "../context/learner-context";
import type { LearnerContextValue } from "../context/learner-context";
import DashboardPage from "../pages/DashboardPage";

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
        <DashboardPage />
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
  last_session_at: new Date().toISOString(),
  total_study_time_minutes: 135,
};

beforeEach(() => {
  mockFetch.mockReset();
});

describe("DashboardPage", () => {
  it("shows loading skeletons then loaded state", async () => {
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
    expect(screen.getByText(/words learned/)).toBeInTheDocument();
    expect(screen.getByText("2h 15m")).toBeInTheDocument();
  });

  it("shows get-started card for language with no state (404)", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ detail: "Not found" }, 404),
    );

    renderPage();

    await waitFor(() => {
      expect(
        screen.getAllByText(/take a placement test to find your level/i).length,
      ).toBeGreaterThan(0);
    });
  });

  it("shows welcome message with learner name", () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ detail: "Not found" }, 404),
    );

    renderPage();
    expect(screen.getByText(/welcome back, alice/i)).toBeInTheDocument();
  });

  it("shows practice and placement links for loaded language", async () => {
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

    const practiceLinks = screen.getAllByRole("link", { name: /practice/i });
    expect(practiceLinks.length).toBeGreaterThan(0);
  });
});
