import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { companyApi } from "../api/company";
import { EmployeeWorkspace } from "../pages/ai/EmployeeWorkspace";

vi.mock("../api/company");

beforeEach(() => {
  vi.mocked(companyApi.workspace).mockResolvedValue({
    data: {
      profile: {
        id: "e1",
        name: "Ritchie",
        code: "WES-EMP-006",
        role: "Backend Engineer AI",
        department: "Engineering",
        authority: "operational",
        provider: "mock",
        status: "Coding",
      },
      current: {
        task: "DEV-0002",
        task_title: "Backend implementation",
        project: "Widget Module",
        sprint: 1,
        branch: "feature/auto-dev-0002",
        repository: "WES Backend",
        context: "Backend implementation",
      },
      performance: { assigned: 3, in_progress: 1, done: 1, stages_performed: 8 },
      inbox: [
        {
          task_code: "DEV-0002",
          title: "Backend implementation — Widget API",
          project: "Widget Module",
          sender: "Hopper",
          priority: "high",
          received: null,
          deadline: null,
          repository: "WES Backend",
          status: "in_progress",
          estimated_hours: 12,
        },
      ],
      tasks: { assigned: ["W-1"], in_progress: ["W-2"], done: ["W-3"] },
      decisions: [
        { at: null, decision: "Coding", stage: "implementation", reason: "MODIFY applied", provider: "mock", status: "completed" },
      ],
      handoffs: [
        { at: null, from: "Ritchie", to: "Dijkstra", reason: "handed off for testing", stage: "testing", result: "delivered" },
      ],
    },
  } as never);
});

describe("EmployeeWorkspace", () => {
  it("renders profile, current context, inbox, decisions and handoffs", async () => {
    render(
      <MemoryRouter initialEntries={["/ai/employees/e1/workspace"]}>
        <Routes>
          <Route path="/ai/employees/:id/workspace" element={<EmployeeWorkspace />} />
        </Routes>
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Ritchie — Workspace")).toBeInTheDocument());
    expect(screen.getByText("feature/auto-dev-0002")).toBeInTheDocument();
    expect(screen.getByText("Backend implementation — Widget API")).toBeInTheDocument();
    expect(screen.getByTestId("decision-row")).toBeInTheDocument();
    expect(screen.getByTestId("handoff-row")).toBeInTheDocument();
  });
});
