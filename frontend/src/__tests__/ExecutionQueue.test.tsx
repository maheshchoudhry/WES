import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { executionApi } from "../api/execution";
import { ExecutionQueue } from "../pages/execution/ExecutionQueue";

vi.mock("../api/execution");

function item(id: string, title: string, status: string) {
  return {
    id,
    ai_employee_id: "e1",
    ai_employee_name: "Ritchie",
    work_item_id: "w1",
    work_item_code: "WORLD-004",
    title,
    description: null,
    priority: "high",
    status,
    position: 0,
    started_at: null,
    completed_at: null,
  };
}

beforeEach(() => {
  vi.mocked(executionApi.queue).mockResolvedValue({
    data: [item("q1", "Implement API endpoint", "queued")],
    meta: { total: 1 },
  } as never);
  vi.mocked(executionApi.advanceQueue).mockResolvedValue({
    data: item("q1", "x", "in_progress"),
  } as never);
});

describe("ExecutionQueue", () => {
  it("lists queue items and advances them", async () => {
    render(<ExecutionQueue />);
    await waitFor(() => expect(screen.getByText("Implement API endpoint")).toBeInTheDocument());
    expect(screen.getByText("Ritchie")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /in progress/i }));
    expect(executionApi.advanceQueue).toHaveBeenCalledWith("q1", "in_progress");
  });
});
