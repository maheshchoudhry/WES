import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { EmployeeDirectoryItem } from "../api/dashboard";
import { OrgSnapshot } from "../components/widgets/OrgSnapshot";
import { StatCard } from "../components/widgets/StatCard";

function emp(id: string, name: string, reports_to_id: string | null): EmployeeDirectoryItem {
  return {
    id,
    employee_code: id,
    full_name: name,
    position: "Role",
    authority: "operational",
    status: "active",
    department_id: null,
    department_name: null,
    reports_to_id,
    manager_name: null,
  };
}

describe("StatCard", () => {
  it("renders label, value, and hint", () => {
    render(<StatCard label="Employees" value={13} hint="live" />);
    expect(screen.getByText("Employees")).toBeInTheDocument();
    expect(screen.getByText("13")).toBeInTheDocument();
    expect(screen.getByText("live")).toBeInTheDocument();
  });
});

describe("OrgSnapshot", () => {
  it("nests reports under their manager", () => {
    const employees = [
      emp("director", "Studio Director", null),
      emp("architect", "Software Architect", "director"),
      emp("engineer", "Backend Engineer", "architect"),
    ];
    const { container } = render(<OrgSnapshot employees={employees} />);
    // One root at the top level of the tree.
    const rootItems = container.querySelectorAll(":scope > ul.org-tree > li");
    expect(rootItems).toHaveLength(1);
    expect(screen.getByText("Studio Director")).toBeInTheDocument();
    expect(screen.getByText("Backend Engineer")).toBeInTheDocument();
  });

  it("shows an empty message with no employees", () => {
    render(<OrgSnapshot employees={[]} />);
    expect(screen.getByText(/no employees to display/i)).toBeInTheDocument();
  });
});
