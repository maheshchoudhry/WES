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
        config: {},
        health: "healthy",
      },
      {
        id: "p2",
        name: "claude",
        display_name: "Anthropic Claude",
        enabled: false,
        is_default: false,
        default_model: "claude-opus-4-8",
        config: { api_key: "***" },
        health: "unavailable",
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
    expect(screen.getByText("Anthropic Claude")).toBeInTheDocument();
    expect(screen.getAllByText("healthy").length).toBeGreaterThan(0);
    // "Default" appears as a column header and the default badge.
    expect(screen.getAllByText("Default").length).toBeGreaterThan(1);
    expect(screen.getByText("BACKEND_ENGINEER")).toBeInTheDocument();
  });
});
