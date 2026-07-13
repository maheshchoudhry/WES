import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { workApi } from "../api/work";
import { ProjectsPage } from "../pages/work/ProjectsPage";

vi.mock("../api/work");

beforeEach(() => {
  vi.mocked(workApi.projects).mockResolvedValue({
    data: [
      {
        id: "p1",
        code: "PROJECT-001",
        name: "WORLD",
        owner_ai_employee_id: "e1",
        owner_name: "Ada",
        status: "active",
        priority: "high",
        repository: "github.com/wes/world",
        tech_stack: "Python, React",
        version: 1,
        task_count: 10,
        created_at: "",
        updated_at: "",
      },
    ],
    meta: { total: 1 },
  } as never);
});

describe("ProjectsPage", () => {
  it("lists projects with owner and task count", async () => {
    render(
      <MemoryRouter>
        <ProjectsPage />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByRole("link", { name: "WORLD" })).toBeInTheDocument());
    expect(screen.getByText("PROJECT-001")).toBeInTheDocument();
    expect(screen.getByText("Ada")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });
});
