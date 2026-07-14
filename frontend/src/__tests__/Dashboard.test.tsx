import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { aiApi } from "../api/ai";
import { dashboardApi } from "../api/dashboard";
import { executionApi } from "../api/execution";
import { knowledgeApi } from "../api/knowledge";
import { orchestrationApi } from "../api/orchestration";
import { workApi } from "../api/work";
import { Dashboard } from "../pages/Dashboard";

vi.mock("../api/dashboard");
vi.mock("../api/ai");
vi.mock("../api/work");
vi.mock("../api/execution");
vi.mock("../api/orchestration");
vi.mock("../api/knowledge");

const company = {
  id: "c1",
  name: "WORLD Engineering Studio",
  slug: "wes",
  company_type: "AI Company",
  purpose: null,
  status: "active",
  department_count: 6,
  employee_count: 13,
};

function renderDashboard() {
  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.mocked(orchestrationApi.founderDashboard).mockResolvedValue({
    data: {
      providers: [{ name: "mock", enabled: true, is_default: true, health: "healthy" }],
      running_executions: 0,
      failed_executions: 1,
      completed_executions: 2,
      execution_queue: 3,
      token_usage: 486,
      estimated_cost: 0,
      avg_runtime_ms: 5,
    },
  } as never);
  vi.mocked(knowledgeApi.founderDashboard).mockResolvedValue({
    data: {
      documents: 8,
      categories: 12,
      pending_reviews: 1,
      approved_documents: 4,
      knowledge_health: "healthy",
      approved_coverage: 0.5,
      recent_knowledge: [],
      most_used: [],
      statistics: {
        total_documents: 8,
        total_categories: 12,
        total_adrs: 2,
        total_views: 29,
        retrievals: 3,
        by_status: { approved: 4 },
        by_type: { coding_standard: 1 },
      },
    },
  } as never);
  vi.mocked(executionApi.founderDashboard).mockResolvedValue({
    data: {
      ai_work_queue: 5,
      queued: 3,
      in_progress: 1,
      pending_reviews: 1,
      completed_work: 1,
      avg_completion_seconds: 3600,
      organization_performance: { total_executions: 1, handoffs: 8 },
    },
  } as never);
  vi.mocked(workApi.founderSummary).mockResolvedValue({
    data: {
      total_projects: 1,
      total_tasks: 10,
      tasks_by_status: { done: 3 },
      tasks_by_priority: {},
      blocked_tasks: 1,
      sprint_progress: [],
      velocity: 44,
      upcoming_deadlines: [],
      ai_workload: {},
    },
  } as never);
  vi.mocked(aiApi.summary).mockResolvedValue({
    data: {
      total_employees: 12,
      department_count: 3,
      role_count: 12,
      by_status: { active: 12 },
      by_department: { Engineering: 8 },
      ceo_present: true,
      organization_health: "healthy",
    },
  } as never);
  vi.mocked(dashboardApi.departments).mockResolvedValue({
    data: [
      {
        id: "d1",
        code: "DEPT-02",
        name: "Engineering",
        focus: "Build",
        status: "active",
        employee_count: 2,
      },
    ],
    meta: { total: 1 },
  } as never);
  vi.mocked(dashboardApi.employees).mockResolvedValue({
    data: [
      {
        id: "e1",
        employee_code: "WES-EMP-004",
        full_name: "Software Architect",
        position: "Software Architect",
        authority: "lead",
        status: "active",
        department_id: "d1",
        department_name: "Engineering",
        reports_to_id: null,
        manager_name: null,
      },
      {
        id: "e2",
        employee_code: "WES-EMP-006",
        full_name: "Backend Engineer",
        position: "Backend Engineer",
        authority: "operational",
        status: "active",
        department_id: "d1",
        department_name: "Engineering",
        reports_to_id: "e1",
        manager_name: "Software Architect",
      },
    ],
    meta: { total: 2 },
  } as never);
  vi.mocked(dashboardApi.activity).mockResolvedValue({
    data: [
      {
        entity_type: "employee",
        action: "created",
        entity_id: "e2",
        label: "WES-EMP-006 — Backend Engineer",
        timestamp: new Date().toISOString(),
      },
    ],
    meta: { total: 1 },
  } as never);
  vi.mocked(dashboardApi.health).mockResolvedValue({
    data: {
      api: "ok",
      database: "connected",
      version: "0.2.0",
      companies: 1,
      departments: 6,
      employees: 13,
    },
  } as never);
});

describe("Dashboard", () => {
  it("renders live company stats and sections", async () => {
    vi.mocked(dashboardApi.stats).mockResolvedValue({
      data: {
        company,
        totals: { departments: 6, employees: 13, active_projects: 0 },
        employees_by_status: { active: 13 },
        employees_by_authority: { lead: 3, operational: 9, executive: 1 },
        departments_by_status: { active: 6 },
      },
    } as never);

    renderDashboard();

    await waitFor(() => expect(screen.getByText("Founder Dashboard")).toBeInTheDocument());
    // Stat values from live data.
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getAllByText("13").length).toBeGreaterThan(0);
    // Sections and widgets.
    expect(screen.getByText("Department Overview")).toBeInTheDocument();
    expect(screen.getByText("Organization Snapshot")).toBeInTheDocument();
    expect(screen.getByText("Recent Activity")).toBeInTheDocument();
    // Employee directory shows manager relationship.
    expect(screen.getAllByText("Software Architect").length).toBeGreaterThan(0);
  });

  it("shows an empty state when no company exists", async () => {
    vi.mocked(dashboardApi.stats).mockResolvedValue({
      data: {
        company: null,
        totals: { departments: 0, employees: 0, active_projects: 0 },
        employees_by_status: {},
        employees_by_authority: {},
        departments_by_status: {},
      },
    } as never);

    renderDashboard();

    await waitFor(() => expect(screen.getByText(/no company exists yet/i)).toBeInTheDocument());
  });
});
