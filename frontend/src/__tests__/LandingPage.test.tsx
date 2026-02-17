import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { BrowserRouter } from "react-router";
import { LearnerProvider } from "../context/LearnerContext";
import LandingPage from "../pages/LandingPage";

function renderPage() {
  return render(
    <BrowserRouter>
      <LearnerProvider>
        <LandingPage />
      </LearnerProvider>
    </BrowserRouter>,
  );
}

describe("LandingPage", () => {
  it("renders hero heading", () => {
    renderPage();
    expect(
      screen.getByRole("heading", { name: /learn ancient greek and latin/i }),
    ).toBeInTheDocument();
  });

  it("shows feature cards", () => {
    renderPage();
    expect(screen.getByText("Adaptive Practice")).toBeInTheDocument();
    expect(screen.getByText("Placement Testing")).toBeInTheDocument();
    expect(screen.getByText("Progress Tracking")).toBeInTheDocument();
    expect(screen.getByText("AI-Powered Feedback")).toBeInTheDocument();
  });

  it("shows language cards with start buttons", () => {
    renderPage();
    expect(screen.getByText("Start Ancient Greek")).toBeInTheDocument();
    expect(screen.getByText("Start Latin")).toBeInTheDocument();
  });

  it("shows Get Started CTA when no learner", () => {
    renderPage();
    expect(
      screen.getByRole("link", { name: /get started/i }),
    ).toBeInTheDocument();
  });
});
