import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { orchestrationApi } from "../api/orchestration";
import { BudgetDashboard } from "../pages/orchestration/BudgetDashboard";

vi.mock("../api/orchestration");

beforeEach(() => {
  vi.mocked(orchestrationApi.budget).mockResolvedValue({
    data: {
      config: {
        daily_cost_limit: 50,
        monthly_cost_limit: 1000,
        max_cost: 5,
        max_tokens: 200000,
        warning_threshold: 0.8,
        hard_stop: true,
        currency: "USD",
      },
      daily_spent: 0.0123,
      monthly_spent: 0.5,
      daily_pct: 0.0002,
      monthly_pct: 0.0005,
      warning: false,
      exceeded: false,
      hard_stop_active: false,
    },
  } as never);
  vi.mocked(orchestrationApi.cost).mockResolvedValue({
    data: [{ key: "p1", label: "mock", tokens: 486, cost: 0 }],
    meta: { group_by: "day", total: 1 },
  } as never);
});

describe("BudgetDashboard", () => {
  it("shows spend, limits, and hard-stop status", async () => {
    render(<BudgetDashboard />);
    await waitFor(() => expect(screen.getByText("Budget Dashboard")).toBeInTheDocument());
    expect(screen.getByText("$0.0123")).toBeInTheDocument();
    expect(screen.getByText("Daily Spent")).toBeInTheDocument();
    expect(screen.getByText("Configure Budget")).toBeInTheDocument();
    // Hard stop is on.
    expect(screen.getByText("On")).toBeInTheDocument();
  });
});
