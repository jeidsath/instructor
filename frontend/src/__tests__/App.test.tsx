import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import App from "../App";

describe("App", () => {
  it("renders the landing page at /", () => {
    render(<App />);
    expect(
      screen.getByRole("heading", { name: /learn ancient greek and latin/i }),
    ).toBeInTheDocument();
  });

  it("shows the Instructor nav link", () => {
    render(<App />);
    expect(
      screen.getByRole("link", { name: /instructor/i }),
    ).toBeInTheDocument();
  });
});
