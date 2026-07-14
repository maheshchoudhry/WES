import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { developmentApi } from "../api/development";
import { DevelopmentDashboard } from "../pages/development/DevelopmentDashboard";

vi.mock("../api/development");

beforeEach(() => {
  vi.mocked(developmentApi.founderDashboard).mockResolvedValue({
    data: {
      running: 1,
      completed: 3,
      failed: 0,
      pending_approvals: 2,
      open_pull_requests: 2,
      total_tasks: 6,
      recent_tasks: [
        {
          id: "t1",
          code: "DEV-0001",
          title: "Add health ping utility",
          description: null,
          status: "pr_ready",
          branch_name: "feature/auto-dev-0001",
          sandbox_path: null,
          repository_id: null,
          error: null,
          duration_ms: 560,
          created_at: null,
        },
      ],
    },
  } as never);
});

describe("DevelopmentDashboard", () => {
  it("shows stats and recent tasks", async () => {
    render(
      <MemoryRouter>
        <DevelopmentDashboard />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Autonomous Development")).toBeInTheDocument());
    expect(screen.getByText("Pending Approvals")).toBeInTheDocument();
    expect(screen.getByText("Add health ping utility")).toBeInTheDocument();
    expect(screen.getByText("DEV-0001")).toBeInTheDocument();
    expect(screen.getByText("Run Autonomous Task")).toBeInTheDocument();
  });
});
