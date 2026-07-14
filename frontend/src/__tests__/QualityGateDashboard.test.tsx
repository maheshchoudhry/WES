import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { qualityApi } from "../api/quality";
import { QualityGateDashboard } from "../pages/quality/QualityGateDashboard";

vi.mock("../api/quality", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/quality")>();
  return {
    ...actual,
    qualityApi: { founderDashboard: vi.fn(), report: vi.fn(), rules: vi.fn() },
  };
});

beforeEach(() => {
  vi.mocked(qualityApi.founderDashboard).mockResolvedValue({
    data: {
      total_gate_runs: 4,
      approval_eligible: 3,
      blocked: 1,
      avg_review_score: 96,
      avg_security_score: 100,
      avg_performance_score: 100,
      open_critical: 0,
      release_ready: 3,
      recent: [
        {
          task_id: "task-12345678",
          overall_score: 100,
          security_score: 100,
          approval_eligible: true,
          critical_count: 0,
        },
      ],
    },
  } as never);
  vi.mocked(qualityApi.report).mockResolvedValue({
    data: {
      gate: {
        id: "g1",
        task_id: "task-12345678",
        status: "passed",
        architecture_score: 100,
        code_score: 100,
        security_score: 100,
        performance_score: 100,
        documentation_score: 100,
        overall_score: 100,
        tests_passed_pct: 100,
        formatting_clean: true,
        lint_clean: true,
        documentation_complete: true,
        critical_count: 0,
        high_count: 0,
        total_findings: 0,
        approval_eligible: true,
        gates: [
          {
            code: "architecture_score",
            name: "Architecture Score ≥ 90",
            value: 100,
            threshold: 90,
            passed: true,
          },
          {
            code: "security_critical",
            name: "Security Critical = 0",
            value: 0,
            threshold: 0,
            passed: true,
          },
        ],
        summary: "clean",
      },
      review_findings: [],
      security_findings: [],
      performance_findings: [],
      dependency_findings: [],
      documentation_findings: [],
      compliance: [],
      metrics: null,
      release_readiness: null,
    },
  } as never);
  vi.mocked(qualityApi.rules).mockResolvedValue({
    data: [
      {
        code: "architecture_score",
        name: "Architecture Score ≥ 90",
        category: "architecture",
        operator: "gte",
        threshold: 90,
        severity: "high",
        enabled: true,
        mandatory: true,
        description: null,
      },
    ],
    meta: { total: 1 },
  } as never);
});

describe("QualityGateDashboard", () => {
  it("shows aggregate stats, latest gate checklist, and rules", async () => {
    render(
      <MemoryRouter>
        <QualityGateDashboard />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Quality Gate Dashboard")).toBeInTheDocument());
    expect(screen.getByText("Approval-Eligible")).toBeInTheDocument();
    expect(screen.getByText("Release Ready")).toBeInTheDocument();
    // Rule + gate name appear.
    expect(screen.getAllByText("Architecture Score ≥ 90").length).toBeGreaterThan(0);
  });
});
