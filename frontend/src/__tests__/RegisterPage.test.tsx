import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { BrowserRouter } from "react-router";
import { LearnerProvider } from "../context/LearnerContext";
import RegisterPage from "../pages/RegisterPage";

const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function renderPage() {
  return render(
    <BrowserRouter>
      <LearnerProvider>
        <RegisterPage />
      </LearnerProvider>
    </BrowserRouter>,
  );
}

beforeEach(() => {
  mockFetch.mockReset();
  localStorage.clear();
});

describe("RegisterPage", () => {
  it("renders the registration form", () => {
    renderPage();
    expect(
      screen.getByRole("heading", { name: /welcome to instructor/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/your name/i)).toBeInTheDocument();
    expect(screen.getByText("Ancient Greek")).toBeInTheDocument();
    expect(screen.getByText("Latin")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /begin learning/i }),
    ).toBeInTheDocument();
  });

  it("shows error when name is empty", async () => {
    renderPage();
    await userEvent.click(screen.getByText("Latin"));
    await userEvent.click(
      screen.getByRole("button", { name: /begin learning/i }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Please enter your name",
    );
  });

  it("shows error when no language selected", async () => {
    renderPage();
    await userEvent.type(screen.getByLabelText(/your name/i), "Alice");
    await userEvent.click(
      screen.getByRole("button", { name: /begin learning/i }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Please select a language",
    );
  });

  it("submits successfully and stores learner", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ id: "abc-123", name: "Alice" }, 201),
    );

    renderPage();
    await userEvent.type(screen.getByLabelText(/your name/i), "Alice");
    await userEvent.click(screen.getByText("Latin"));
    await userEvent.click(
      screen.getByRole("button", { name: /begin learning/i }),
    );

    await waitFor(() => {
      expect(localStorage.getItem("instructor_learner")).toContain("Alice");
    });
  });

  it("shows API error on failure", async () => {
    mockFetch.mockResolvedValue(
      jsonResponse({ detail: "Validation error" }, 422),
    );

    renderPage();
    await userEvent.type(screen.getByLabelText(/your name/i), "Alice");
    await userEvent.click(screen.getByText("Ancient Greek"));
    await userEvent.click(
      screen.getByRole("button", { name: /begin learning/i }),
    );

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("Validation error");
    });
  });
});
