import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { repositoryApi } from "../api/repository";
import { RepositoryDashboard } from "../pages/repository/RepositoryDashboard";

vi.mock("../api/repository");

const repo = {
  id: "r1",
  slug: "wes-backend",
  name: "WES Backend",
  root_path: "/x",
  description: null,
  primary_language: "python",
  frameworks: ["fastapi", "sqlalchemy"],
  status: "indexed",
  last_scanned_at: null,
  metrics: {
    file_count: 130,
    module_count: 20,
    symbol_count: 900,
    class_count: 120,
    function_count: 600,
    route_count: 80,
    model_count: 40,
    line_count: 12000,
    dependency_count: 400,
    test_file_count: 20,
    technical_debt: 3,
    health_score: 72,
    languages: { python: 130 },
  },
};

beforeEach(() => {
  vi.mocked(repositoryApi.list).mockResolvedValue({ data: [repo], meta: { total: 1 } } as never);
  vi.mocked(repositoryApi.dashboard).mockResolvedValue({
    data: {
      ...repo,
      architecture: [
        {
          layer: "service",
          name: "Service",
          file_count: 30,
          symbol_count: 200,
          description: "30 files",
        },
      ],
      external_dependencies: [{ package: "fastapi", usages: 40 }],
      issues: [
        { severity: "low", category: "maintainability", message: "Large file", file_path: "x.py" },
      ],
      todo_count: 5,
    },
  } as never);
});

describe("RepositoryDashboard", () => {
  it("shows metrics, architecture, and dependencies", async () => {
    render(
      <MemoryRouter>
        <RepositoryDashboard />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Repository Intelligence")).toBeInTheDocument());
    expect(screen.getByText("130")).toBeInTheDocument(); // files
    expect(screen.getByText("900")).toBeInTheDocument(); // symbols
    expect(screen.getByText("Service: 30 files")).toBeInTheDocument();
    expect(screen.getByText("fastapi")).toBeInTheDocument();
    expect(screen.getByText("Large file")).toBeInTheDocument();
  });
});
