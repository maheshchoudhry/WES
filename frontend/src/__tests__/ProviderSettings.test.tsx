import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { orchestrationApi } from "../api/orchestration";
import { ProviderSettings } from "../pages/orchestration/ProviderSettings";

vi.mock("../api/orchestration");

beforeEach(() => {
  vi.mocked(orchestrationApi.providers).mockResolvedValue({
    data: [
      {
        id: "p1",
        name: "mock",
        display_name: "Mock Provider",
        enabled: true,
        is_default: true,
        default_model: "mock-1",
        active_model: "mock-1",
        priority: 10,
        config: {},
        has_secret: false,
        secret_hint: null,
        models: [
          {
            id: "m1",
            code: "mock-1",
            display_name: "Mock 1",
            is_default: true,
            enabled: true,
            context_window: 8000,
            input_cost_per_1k: 0,
            output_cost_per_1k: 0,
          },
        ],
        health: "healthy",
        health_detail: null,
      },
      {
        id: "p2",
        name: "claude",
        display_name: "Anthropic Claude",
        enabled: false,
        is_default: false,
        default_model: "claude-opus-4-8",
        active_model: "claude-opus-4-8",
        priority: 20,
        config: { api_key: "***" },
        has_secret: true,
        secret_hint: "••••••7654",
        models: [],
        health: "unavailable",
        health_detail: "not configured",
      },
    ],
    meta: { total: 2 },
  } as never);
  vi.mocked(orchestrationApi.roleMappings).mockResolvedValue({
    data: { BACKEND_ENGINEER: "mock" },
  } as never);
});

describe("ProviderSettings", () => {
  it("lists providers with health and default, plus role mappings", async () => {
    render(<ProviderSettings />);
    await waitFor(() => expect(screen.getByText("Mock Provider")).toBeInTheDocument());
    // Claude appears in the providers table and the credentials section.
    expect(screen.getAllByText("Anthropic Claude").length).toBeGreaterThan(0);
    expect(screen.getAllByText("healthy").length).toBeGreaterThan(0);
    // "Default" appears as a column header and the default badge.
    expect(screen.getAllByText("Default").length).toBeGreaterThan(1);
    expect(screen.getByText("BACKEND_ENGINEER")).toBeInTheDocument();
  });
});
