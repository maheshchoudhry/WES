import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { learningApi } from "../api/learning";
import { SelfLearning } from "../pages/SelfLearning";

vi.mock("../api/learning");

beforeEach(() => {
  vi.mocked(learningApi.rules).mockResolvedValue({
    data: [
      { id: "r1", kind: "coding_standard", rule: "python changes must compile and pass tests before a PR", dimension: "test_coverage", occurrences: 3, applied_count: 2, evidence: "DEV-0001: 2 tests passed", active: true },
      { id: "r2", kind: "bug_prevention", rule: "Avoid unsafe eval patterns", dimension: "security", occurrences: 1, applied_count: 0, evidence: "review of DEV-0002", active: true },
    ],
    meta: { total: 2 },
  } as never);
  vi.mocked(learningApi.summary).mockResolvedValue({
    data: { total_rules: 2, total_applications: 2, by_kind: { coding_standard: 1, bug_prevention: 1 } },
  } as never);
});

describe("SelfLearning", () => {
  it("renders learned rules with occurrences and applications", async () => {
    render(
      <MemoryRouter>
        <SelfLearning />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Self-Learning")).toBeInTheDocument());
    expect(
      screen.getByText("python changes must compile and pass tests before a PR"),
    ).toBeInTheDocument();
    expect(screen.getByText("Avoid unsafe eval patterns")).toBeInTheDocument();
    expect(screen.getByText("Applications")).toBeInTheDocument();
  });
});
