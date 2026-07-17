import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { notificationsApi } from "../api/notifications";
import { Notifications } from "../pages/Notifications";

vi.mock("../api/notifications");

beforeEach(() => {
  vi.mocked(notificationsApi.list).mockResolvedValue({
    data: [
      {
        id: "n1",
        kind: "approval_needed",
        title: "DEV-0001 awaits your approval",
        message: "Reached PR — Founder approval required.",
        severity: "action",
        entity_type: "dev_task",
        entity_id: "t1",
        read: false,
        created_at: null,
      },
      {
        id: "n2",
        kind: "deployment",
        title: "Deployment to staging complete",
        message: "Pipeline PIPE-0001 finished (passed).",
        severity: "info",
        entity_type: "dev_task",
        entity_id: "t1",
        read: false,
        created_at: null,
      },
    ],
    meta: { total: 2 },
  } as never);
  vi.mocked(notificationsApi.markAllRead).mockResolvedValue({ data: { marked: 2 } } as never);
});

describe("Notifications", () => {
  it("renders founder notifications from the autonomous chain", async () => {
    render(
      <MemoryRouter>
        <Notifications />
      </MemoryRouter>,
    );
    await waitFor(() => expect(screen.getByText("Notifications")).toBeInTheDocument());
    expect(screen.getByText("DEV-0001 awaits your approval")).toBeInTheDocument();
    expect(screen.getByText("Deployment to staging complete")).toBeInTheDocument();
    expect(screen.getByText("2 unread · autonomous-chain milestones and approvals.")).toBeInTheDocument();
    expect(screen.getAllByTestId("notif-item")).toHaveLength(2);
  });
});
