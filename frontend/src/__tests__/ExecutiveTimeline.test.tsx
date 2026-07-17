import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { companyApi } from "../api/company";
import { ExecutiveTimeline } from "../pages/company/ExecutiveTimeline";

vi.mock("../api/company");

beforeEach(() => {
  vi.mocked(companyApi.timeline).mockResolvedValue({
    data: [
      { at: "2026-07-15T10:00:00", actor: "Founder", type: "project_created", title: "Founder created project VIS-1" },
      { at: "2026-07-15T10:01:00", actor: "Ritchie", type: "stage", title: "Ritchie — Coding on DEV-0002" },
    ],
    meta: { total: 2 },
  } as never);
  vi.mocked(companyApi.conversations).mockResolvedValue({
    data: [
      { at: "2026-07-15T10:01:00", from: "Lovelace", to: "Hopper", from_role: "PM", to_role: "Architect", stage: "repo_analysis", message: "handed off to Architect", task: "DEV-0002", status: "delivered" },
    ],
    meta: { total: 1 },
  } as never);
});

describe("ExecutiveTimeline", () => {
  it("renders runtime events and agent conversations", async () => {
    render(
      <MemoryRouter>
        <ExecutiveTimeline />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Executive Timeline")).toBeInTheDocument());
    expect(screen.getByText("Founder created project VIS-1")).toBeInTheDocument();
    expect(screen.getByText("Ritchie — Coding on DEV-0002")).toBeInTheDocument();
    expect(screen.getAllByTestId("timeline-event")).toHaveLength(2);
    // Agent conversation from a real handoff.
    expect(screen.getByTestId("convo-item")).toBeInTheDocument();
  });
});
