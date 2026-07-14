import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { developmentApi } from "../api/development";
import { devopsApi } from "../api/devops";
import { PipelineDashboard } from "../pages/devops/PipelineDashboard";

vi.mock("../api/devops");
vi.mock("../api/development");

beforeEach(() => {
  vi.mocked(devopsApi.founderDashboard).mockResolvedValue({
    data: {
      total_pipelines: 1,
      running: 0,
      awaiting_production: 1,
      passed: 0,
      failed: 0,
      deployments: 1,
      production_deployments: 0,
      releases: 1,
      open_incidents: 0,
      system_health: {
        overall_status: "healthy",
        app_status: "healthy",
        api_status: "healthy",
        db_status: "healthy",
        provider_status: "healthy",
        cpu_pct: 12,
        memory_pct: 44,
        disk_pct: 30,
        queue_depth: 0,
        response_time_ms: 3,
        created_at: null,
      },
      recent_pipelines: [
        {
          id: "p1",
          code: "PIPE-0001",
          task_id: "t1",
          status: "awaiting_production",
          environment_target: "staging",
          current_stage: "production_approval",
          triggered_by: "DevOps",
          duration_ms: 900,
          error: null,
          created_at: null,
          stages: [
            { stage: "build", status: "passed", detail: "checksum abc" },
            { stage: "staging_deploy", status: "passed", detail: "deployed" },
            { stage: "production_approval", status: "pending", detail: "awaiting" },
          ],
        },
      ],
    },
  } as never);
  vi.mocked(developmentApi.tasks).mockResolvedValue({
    data: [
      {
        id: "t1",
        code: "DEV-0001",
        title: "Add health ping utility",
        description: null,
        status: "approved",
        branch_name: "feature/auto-dev-0001",
        sandbox_path: null,
        repository_id: null,
        error: null,
        duration_ms: 500,
        created_at: null,
      },
    ],
    meta: { total: 1 },
  } as never);
});

describe("PipelineDashboard", () => {
  it("shows pipeline stats and the latest pipeline stages", async () => {
    render(
      <MemoryRouter>
        <PipelineDashboard />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("CI/CD Pipeline")).toBeInTheDocument());
    expect(screen.getByText("Awaiting Production")).toBeInTheDocument();
    expect(screen.getByText("Run Pipeline")).toBeInTheDocument();
    // Latest pipeline card with production approval action.
    expect(screen.getByText("Approve Production Deploy")).toBeInTheDocument();
    expect(screen.getAllByText(/PIPE-0001/).length).toBeGreaterThan(0);
  });
});
