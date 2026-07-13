import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { aiApi } from "../api/ai";
import { AIDashboard } from "../pages/ai/AIDashboard";

vi.mock("../api/ai");

beforeEach(() => {
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
