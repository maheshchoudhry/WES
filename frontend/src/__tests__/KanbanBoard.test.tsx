import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { workApi } from "../api/work";
import { KanbanBoard } from "../pages/work/KanbanBoard";

vi.mock("../api/work");

function task(id: string, code: string, title: string, status: string) {
  return {
    id,
    task_code: code,
    title,
    description: null,
    acceptance_criteria: null,
    priority: "high",
    status,
    estimated_hours: null,
    actual_hours: null,
    project_id: "p1",
    project_code: "PROJECT-001",
    sprint_id: null,
    sprint_number: 3,
    milestone_id: null,
    milestone_name: null,
    assigned_ai_employee_id: "e1",
    assigned_name: "Resig",
    reviewer_ai_employee_id: null,
    reviewer_name: null,
    created_at: "",
    updated_at: "",
  };
}

beforeEach(() => {
  vi.mocked(workApi.kanban).mockResolvedValue({
    data: [
      { status: "backlog", count: 0, tasks: [] },
      {
        status: "in_progress",
        count: 1,
        tasks: [task("t1", "WORLD-004", "Build dashboard UI", "in_progress")],
      },
      { status: "done", count: 0, tasks: [] },
    ],
  } as never);
});

describe("KanbanBoard", () => {
  it("renders columns and cards", async () => {
    render(
      <MemoryRouter>
        <KanbanBoard />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Task Board")).toBeInTheDocument());
    expect(screen.getAllByText("In Progress").length).toBeGreaterThan(0);
    expect(screen.getByRole("link", { name: "Build dashboard UI" })).toBeInTheDocument();
    expect(screen.getByText("Resig")).toBeInTheDocument();
  });
});
