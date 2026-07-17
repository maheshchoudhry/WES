import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { developmentApi } from "../api/development";
import { AITeam } from "../pages/development/AITeam";

vi.mock("../api/development");

beforeEach(() => {
  vi.mocked(developmentApi.team).mockResolvedValue({
    data: [
      {
        employee: "Ritchie",
        employee_code: "WES-EMP-006",
        role: "Backend Engineer AI",
        authority: "operational",
        provider: "mock",
        responsibilities: ["Implement backend services"],
        decision_rules: ["All code must compile and tests must pass."],
      },
      {
        employee: "Ada",
        employee_code: "WES-EMP-001",
        role: "AI CEO",
        authority: "executive",
        provider: "mock",
        responsibilities: ["Set company direction"],
        decision_rules: ["Approve only work aligned with the business objective."],
      },
    ],
    meta: { total: 2 },
  } as never);
});

describe("AITeam", () => {
  it("renders acting employees with role, authority, provider and policy", async () => {
    render(
      <MemoryRouter>
        <AITeam />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("AI Engineering Team")).toBeInTheDocument());
    expect(screen.getByText("Ritchie")).toBeInTheDocument();
    expect(screen.getByText("Ada")).toBeInTheDocument();
    expect(screen.getByText("Backend Engineer AI")).toBeInTheDocument();
    expect(screen.getByText("All code must compile and tests must pass.")).toBeInTheDocument();
    expect(screen.getAllByText("mock").length).toBeGreaterThan(0);
  });
});
