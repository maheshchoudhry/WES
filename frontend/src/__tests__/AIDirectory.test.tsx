import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { aiApi } from "../api/ai";
import { AIDirectory } from "../pages/ai/AIDirectory";

vi.mock("../api/ai");

function emp(id: string, code: string, name: string, dept: string, deptId: string) {
  return {
    id,
    employee_code: code,
    name,
    department_id: deptId,
    department_name: dept,
    role_id: "r",
    role_title: "Engineer",
    role_level: "operational",
    manager_id: null,
    manager_name: "Ada",
    authority: "operational",
    decision_scope: null,
    status: "active",
    version: 1,
    responsibilities: [],
    capabilities: [],
    kpis: [],
    created_at: "",
    updated_at: "",
  };
}

beforeEach(() => {
  vi.mocked(aiApi.listEmployees).mockResolvedValue({
    data: [
      emp("1", "AI-EMP-001", "Ada", "Executive", "d1"),
      emp("2", "AI-EMP-005", "Ritchie", "Engineering", "d3"),
    ],
    meta: { total: 2 },
  } as never);
  vi.mocked(aiApi.departments).mockResolvedValue({
    data: [
      { id: "d1", code: "AI-DEPT-01", name: "Executive", focus: null, status: "active" },
      { id: "d3", code: "AI-DEPT-03", name: "Engineering", focus: null, status: "active" },
    ],
    meta: { total: 2 },
  } as never);
});

function renderDir() {
  return render(
    <MemoryRouter>
      <AIDirectory />
    </MemoryRouter>,
  );
}

describe("AIDirectory", () => {
  it("lists AI employees", async () => {
    renderDir();
    await waitFor(() => expect(screen.getByRole("link", { name: "Ada" })).toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Ritchie" })).toBeInTheDocument();
  });

  it("filters by search", async () => {
    renderDir();
    await waitFor(() => expect(screen.getByRole("link", { name: "Ada" })).toBeInTheDocument());
    await userEvent.type(screen.getByLabelText(/search ai employees/i), "ritchie");
    expect(screen.queryByRole("link", { name: "Ada" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ritchie" })).toBeInTheDocument();
  });
});
