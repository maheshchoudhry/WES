import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { companiesApi } from "../api/companies";
import { departmentsApi } from "../api/departments";
import { employeesApi } from "../api/employees";
import { CompanyOverview } from "../pages/CompanyOverview";

vi.mock("../api/companies");
vi.mock("../api/departments");
vi.mock("../api/employees");

const company = {
  id: "c1",
  name: "WORLD Engineering Studio",
  slug: "wes",
  company_type: "AI Company",
  purpose: "Build software",
  description: null,
  status: "active",
  created_at: "",
  updated_at: "",
};

beforeEach(() => {
  vi.mocked(departmentsApi.list).mockResolvedValue({ data: [], meta: { total: 6 } } as never);
  vi.mocked(employeesApi.list).mockResolvedValue({ data: [], meta: { total: 13 } } as never);
});

describe("CompanyOverview", () => {
  it("shows the company and its department/employee counts", async () => {
    vi.mocked(companiesApi.list).mockResolvedValue({
      data: [company],
      meta: { total: 1 },
    } as never);

    render(<CompanyOverview />);

    await waitFor(() =>
      expect(screen.getByText("WORLD Engineering Studio")).toBeInTheDocument(),
    );
    expect(screen.getByText("6")).toBeInTheDocument();
    expect(screen.getByText("13")).toBeInTheDocument();
  });

  it("prompts to create a company when none exists", async () => {
    vi.mocked(companiesApi.list).mockResolvedValue({ data: [], meta: { total: 0 } } as never);

    render(<CompanyOverview />);

    await waitFor(() =>
      expect(screen.getByRole("button", { name: /create company/i })).toBeInTheDocument(),
    );
  });
});
