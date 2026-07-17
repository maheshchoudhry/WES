import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { workApi } from "../api/work";
import { ProjectPlan } from "../pages/work/ProjectPlan";

vi.mock("../api/work");

const plan = {
  project: {
    id: "p1",
    code: "PROJ-2",
    name: "Inventory Module",
    business_objective: "Real-time inventory management",
    plan_status: "decomposed",
    status: "planning",
  },
  business_analysis: {
    analyst: "Ada",
    vision: "Deliver a real-time inventory capability.",
    scope: { in_scope: ["Inventory API", "Dashboard"], out_of_scope: ["Payments"] },
    risks: ["Integration risk", "Timeline uncertainty"],
    architecture_proposal: "Extend the layered architecture.",
  },
  epics: [{ id: "e1", name: "Inventory API", status: "pending" }],
  sprints: [{ sprint_number: 1, goal: "Deliver epic: Inventory API", status: "planned" }],
  tasks: [
    {
      task_code: "PROJ-2-T001",
      title: "Backend implementation — Inventory API",
      assignee: "Ritchie",
      reviewer: "Hopper",
      estimated_hours: 12,
      status: "backlog",
    },
  ],
  totals: { epics: 1, sprints: 1, tasks: 1, estimated_hours: 12 },
};

beforeEach(() => {
  vi.mocked(workApi.plan).mockResolvedValue({ data: plan } as never);
  vi.mocked(workApi.approvePlan).mockResolvedValue({
    data: { ...plan, project: { ...plan.project, plan_status: "approved" } },
  } as never);
});

function renderPlan() {
  return render(
    <MemoryRouter initialEntries={["/projects/p1/plan"]}>
      <Routes>
        <Route path="/projects/:id/plan" element={<ProjectPlan />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProjectPlan (AI CEO analysis)", () => {
  it("renders the AI CEO analysis and decomposition", async () => {
    renderPlan();
    await waitFor(() =>
      expect(screen.getByText("AI CEO Analysis — Inventory Module")).toBeInTheDocument(),
    );
    expect(screen.getByText("Ada")).toBeInTheDocument();
    expect(screen.getByText("Business Analysis (AI CEO)")).toBeInTheDocument();
    expect(screen.getByText("Deliver a real-time inventory capability.")).toBeInTheDocument();
    expect(screen.getByText("Integration risk")).toBeInTheDocument();
    // Decomposition table with a real assignee.
    expect(screen.getByText("PROJ-2-T001")).toBeInTheDocument();
    expect(screen.getByText("Ritchie")).toBeInTheDocument();
  });

  it("lets the Founder approve the plan", async () => {
    renderPlan();
    await waitFor(() => expect(screen.getByText("Approve Plan")).toBeInTheDocument());
    fireEvent.click(screen.getByText("Approve Plan"));
    await waitFor(() => expect(workApi.approvePlan).toHaveBeenCalledWith("p1"));
  });
});
