import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { workApi } from "../api/work";
import { ProjectIntake } from "../pages/work/ProjectIntake";

vi.mock("../api/work");

beforeEach(() => {
  vi.mocked(workApi.createProject).mockResolvedValue({
    data: { id: "p1", code: "PROJ-2", name: "Inventory", plan_status: null },
  } as never);
  vi.mocked(workApi.decompose).mockResolvedValue({ data: {} } as never);
});

describe("ProjectIntake", () => {
  it("captures intake fields and submits to the AI CEO", async () => {
    render(
      <MemoryRouter initialEntries={["/projects/new"]}>
        <Routes>
          <Route path="/projects/new" element={<ProjectIntake />} />
          <Route path="/projects/:id/plan" element={<div>PLAN PAGE</div>} />
        </Routes>
      </MemoryRouter>,
    );

    expect(screen.getByText("New Project — Founder Intake")).toBeInTheDocument();
    // Required professional intake fields exist.
    expect(screen.getByLabelText("Project Number")).toBeInTheDocument();
    expect(screen.getByLabelText("Project Name")).toBeInTheDocument();
    expect(screen.getByLabelText("Business Objective")).toBeInTheDocument();
    expect(screen.getByLabelText("Detailed Description")).toBeInTheDocument();
    expect(screen.getByLabelText("Acceptance Criteria")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Project Number"), { target: { value: "PROJ-2" } });
    fireEvent.change(screen.getByLabelText("Project Name"), { target: { value: "Inventory" } });
    fireEvent.change(screen.getByLabelText("Business Objective"), {
      target: { value: "Real-time inventory" },
    });
    fireEvent.change(screen.getByLabelText("Expected Deliverables (one per line)"), {
      target: { value: "Inventory API\nInventory Dashboard" },
    });
    fireEvent.click(screen.getByText("Submit to AI CEO"));

    await waitFor(() => expect(screen.getByText("PLAN PAGE")).toBeInTheDocument());
    // Submitted with intake + decomposed (sent to AI CEO).
    expect(workApi.createProject).toHaveBeenCalledWith(
      expect.objectContaining({
        code: "PROJ-2",
        business_objective: "Real-time inventory",
        deliverables: ["Inventory API", "Inventory Dashboard"],
      }),
    );
    expect(workApi.decompose).toHaveBeenCalledWith("p1");
  });
});
