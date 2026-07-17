import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { auditApi } from "../api/audit";
import { AuditLogs } from "../pages/AuditLogs";

vi.mock("../api/audit");

beforeEach(() => {
  vi.mocked(auditApi.list).mockResolvedValue({
    data: [
      { id: "a1", action: "login", actor: "founder@wes.studio", category: "auth", entity_type: "employee", entity_id: "e1", ip: "127.0.0.1", severity: "info", detail: null, created_at: "2026-07-15T10:00:00" },
      { id: "a2", action: "login_failed", actor: "x@wes.studio", category: "security", entity_type: null, entity_id: null, ip: "10.0.0.9", severity: "warning", detail: null, created_at: "2026-07-15T10:01:00" },
      { id: "a3", action: "pr_approval", actor: "Founder", category: "approval", entity_type: "dev_task", entity_id: "t1", ip: null, severity: "info", detail: "decision=approved override=False", created_at: "2026-07-15T10:02:00" },
    ],
    meta: { total: 3 },
  } as never);
});

describe("AuditLogs", () => {
  it("renders privileged actions and security events", async () => {
    render(
      <MemoryRouter>
        <AuditLogs />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Audit Logs")).toBeInTheDocument());
    expect(screen.getByText("login_failed")).toBeInTheDocument();
    expect(screen.getByText("pr_approval")).toBeInTheDocument();
    expect(screen.getByText("decision=approved override=False")).toBeInTheDocument();
  });
});
