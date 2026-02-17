import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { MemoryRouter, Route, Routes } from "react-router";
import { LearnerContext } from "../context/learner-context";
import type { LearnerContextValue } from "../context/learner-context";
import PlacementTestPage from "../pages/PlacementTestPage";

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
    <MemoryRouter initialEntries={["/placement/latin"]}>
      <LearnerContext value={ctx}>
        <Routes>
          <Route
            path="/placement/:language"
            element={<PlacementTestPage />}
          />
        </Routes>
      </LearnerContext>
    </MemoryRouter>,
  );
}

const vocabSets = [
  { set_name: "core-1", language: "latin", item_count: 50 },
];

const grammarConcepts = [
  {
    name: "first-declension",
    category: "morphology",
    subcategory: "nouns",
    difficulty_level: 1,
    prerequisite_names: [],
  },
];

beforeEach(() => {
  mockFetch.mockReset();
});

describe("PlacementTestPage", () => {
  it("loads curriculum and shows first probe", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/vocabulary")) {
        return Promise.resolve(jsonResponse(vocabSets));
      }
      return Promise.resolve(jsonResponse(grammarConcepts));
    });

    renderPage();

    await waitFor(() => {
      expect(
        screen.getByText(/let's see what you already know/i),
      ).toBeInTheDocument();
    });

    expect(screen.getByText(/question 1 of/i)).toBeInTheDocument();
  });

  it("advances through probes and shows results", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/vocabulary")) {
        return Promise.resolve(jsonResponse(vocabSets));
      }
      if (url.includes("/grammar")) {
        return Promise.resolve(jsonResponse(grammarConcepts));
      }
      // POST /api/placement
      return Promise.resolve(
        jsonResponse({
          total_score: 0.6,
          vocabulary_score: 0.7,
          grammar_score: 0.5,
          reading_score: 0.6,
          starting_unit: 3,
        }),
      );
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/question 1 of/i)).toBeInTheDocument();
    });

    // Click through all probes (there should be 2: 1 vocab + 1 grammar)
    const buttons = screen.getAllByRole("button");
    await userEvent.click(buttons[0]); // Answer first probe

    // If there's a second probe, answer it too
    await waitFor(() => {
      const heading = screen.queryByText("Placement Results");
      if (!heading) {
        // Still probing — answer next
        const nextButtons = screen.getAllByRole("button");
        return userEvent.click(nextButtons[0]);
      }
    });

    await waitFor(() => {
      expect(screen.getByText("Placement Results")).toBeInTheDocument();
    });

    expect(screen.getByText(/unit 3/i)).toBeInTheDocument();
  });

  it("shows error when curriculum fails to load", async () => {
    mockFetch.mockRejectedValue(new Error("Network error"));

    renderPage();

    await waitFor(() => {
      expect(
        screen.getByText(/failed to load curriculum data/i),
      ).toBeInTheDocument();
    });
  });
});
