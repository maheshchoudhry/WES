import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { aiApi } from "../api/ai";
import { executionApi } from "../api/execution";
import { knowledgeApi } from "../api/knowledge";
import { workApi } from "../api/work";
import { AIDashboard } from "../pages/ai/AIDashboard";

vi.mock("../api/ai");
vi.mock("../api/work");
vi.mock("../api/execution");
vi.mock("../api/knowledge");

beforeEach(() => {
  vi.mocked(knowledgeApi.aiDashboard).mockResolvedValue({
    data: {
      suggested_knowledge: [],
      recent_knowledge: [],
      architecture_references: [],
      coding_standards: [
        {
          id: "k1",
          code: "KB-0002",
          title: "Backend Coding Standard",
          doc_type: "coding_standard",
          summary: null,
        },
      ],
      sop_recommendations: [],
      organization_memory: [],
      related_documents: [],
    },
  } as never);
  vi.mocked(executionApi.aiDashboard).mockResolvedValue({
    data: {
      inbox: 8,
      current_work: 1,
      execution_queue: 5,
      review_queue: 1,
      history: 2,
      work_by_employee: {},
    },
  } as never);
  vi.mocked(workApi.aiSummary).mockResolvedValue({
    data: {
      assigned_work: 5,
      current_tasks: 1,
      completed_work: 3,
      team_capacity: { team_size: 12, open_tasks: 5, avg_load: 0.42 },
      work_distribution: {},
      department_load: { Engineering: 5 },
    },
  } as never);
  vi.mocked(aiApi.summary).mockResolvedValue({
    data: {
      total_employees: 12,
      department_count: 3,
      role_count: 12,
      by_status: { active: 12 },
      by_department: { Executive: 3, Product: 1, Engineering: 8 },
      ceo_present: true,
      organization_health: "healthy",
    },
  } as never);
  vi.mocked(aiApi.departmentView).mockResolvedValue({
    data: [
      {
        id: "d1",
        code: "AI-DEPT-01",
        name: "Executive",
        focus: "Lead",
        employee_count: 3,
        employees: [],
      },
    ],
    meta: { total: 1 },
  } as never);
});

describe("AIDashboard", () => {
  it("renders AI organization summary stats", async () => {
    render(
      <MemoryRouter>
        <AIDashboard />
      </MemoryRouter>,
    );
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "AI Company" })).toBeInTheDocument(),
    );
    expect(screen.getByText("AI Employees")).toBeInTheDocument();
    expect(screen.getAllByText("12").length).toBeGreaterThan(0);
    expect(screen.getByText("healthy")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Executive" })).toBeInTheDocument();
  });
});
