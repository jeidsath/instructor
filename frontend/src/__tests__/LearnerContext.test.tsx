import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, beforeEach } from "vitest";
import { LearnerProvider } from "../context/LearnerContext";
import { useLearner } from "../hooks/useLearner";

function TestConsumer() {
  const { learner, setLearner, clearLearner } = useLearner();
  return (
    <div>
      <span data-testid="name">{learner?.name ?? "none"}</span>
      <button onClick={() => setLearner({ id: "1", name: "Alice" })}>
        login
      </button>
      <button onClick={clearLearner}>logout</button>
    </div>
  );
}

beforeEach(() => {
  localStorage.clear();
});

describe("LearnerContext", () => {
  it("starts with no learner", () => {
    render(
      <LearnerProvider>
        <TestConsumer />
      </LearnerProvider>,
    );
    expect(screen.getByTestId("name")).toHaveTextContent("none");
  });

  it("sets and persists learner", async () => {
    render(
      <LearnerProvider>
        <TestConsumer />
      </LearnerProvider>,
    );

    await userEvent.click(screen.getByText("login"));
    expect(screen.getByTestId("name")).toHaveTextContent("Alice");
    expect(localStorage.getItem("instructor_learner")).toContain("Alice");
  });

  it("clears learner", async () => {
    render(
      <LearnerProvider>
        <TestConsumer />
      </LearnerProvider>,
    );

    await userEvent.click(screen.getByText("login"));
    await userEvent.click(screen.getByText("logout"));
    expect(screen.getByTestId("name")).toHaveTextContent("none");
    expect(localStorage.getItem("instructor_learner")).toBeNull();
  });

  it("restores learner from localStorage on mount", () => {
    localStorage.setItem(
      "instructor_learner",
      JSON.stringify({ id: "2", name: "Bob" }),
    );

    render(
      <LearnerProvider>
        <TestConsumer />
      </LearnerProvider>,
    );

    expect(screen.getByTestId("name")).toHaveTextContent("Bob");
  });
});
