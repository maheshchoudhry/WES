import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { companiesApi } from "../api/companies";
import { departmentsApi } from "../api/departments";
import { DepartmentsPage } from "../pages/DepartmentsPage";

vi.mock("../api/companies");
vi.mock("../api/departments");

const company = {
  id: "c1",
  name: "WES",
  slug: "wes",
  company_type: "AI",
  purpose: null,
  description: null,
  status: "active",
  created_at: "",
  updated_at: "",
};

beforeEach(() => {
  vi.mocked(companiesApi.list).mockResolvedValue({ data: [company], meta: { total: 1 } } as never);
});

describe("DepartmentsPage", () => {
  it("renders departments in a table", async () => {
    vi.mocked(departmentsApi.list).mockResolvedValue({
      data: [
        {
          id: "d1",
          company_id: "c1",
          code: "DEPT-02",
          name: "Engineering",
          focus: "Build",
          status: "active",
          created_at: "",
          updated_at: "",
        },
      ],
      meta: { total: 1 },
    } as never);

    render(<DepartmentsPage />);

    await waitFor(() => expect(screen.getByText("Engineering")).toBeInTheDocument());
    expect(screen.getByText("DEPT-02")).toBeInTheDocument();
  });

  it("shows an empty state when there are no departments", async () => {
    vi.mocked(departmentsApi.list).mockResolvedValue({ data: [], meta: { total: 0 } } as never);

    render(<DepartmentsPage />);

    await waitFor(() =>
      expect(screen.getByText(/no departments yet/i)).toBeInTheDocument(),
    );
  });
});
