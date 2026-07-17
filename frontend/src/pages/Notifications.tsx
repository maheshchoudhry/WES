import { notificationsApi, type Notification } from "../api/notifications";
import { Empty, ErrorNotice, Loading } from "../components/States";
import { SectionCard } from "../components/widgets";
import { useAsync } from "../hooks/useAsync";

const KIND_BADGE: Record<string, string> = {
  approval_needed: "prio-high",
  deployment: "badge-active",
  project_execution: "prio-medium",
};

/** Founder notifications (Phase 4) — autonomous-chain milestones that need the
 * Founder's attention (approvals) or report progress (deployments). */
export function Notifications() {
  const { data, loading, error, reload } = useAsync<Notification[]>(
    () => notificationsApi.list().then((r) => r.data),
    [],
  );

  async function markAll() {
    await notificationsApi.markAllRead();
    reload();
  }
  async function markOne(id: string) {
    await notificationsApi.markRead(id);
    reload();
  }

  if (loading) return <Loading label="Loading notifications…" />;
  if (error) return <ErrorNotice message={error} />;
  const items = data ?? [];
  const unread = items.filter((n) => !n.read).length;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Notifications</h1>
          <p>{unread} unread · autonomous-chain milestones and approvals.</p>
        </div>
        {unread > 0 && (
          <button className="btn" onClick={markAll}>
            Mark all read
          </button>
        )}
      </div>

      <SectionCard title="Inbox">
        {items.length === 0 ? (
          <Empty message="No notifications yet." />
        ) : (
          <div className="mini-list">
            {items.map((n) => (
              <div
                key={n.id}
                className="notif-item"
                style={{ opacity: n.read ? 0.55 : 1 }}
                data-testid="notif-item"
              >
                <div style={{ minWidth: 0 }}>
                  <div className="notif-title">
                    <span className={`badge ${KIND_BADGE[n.kind] ?? "prio-low"}`}>{n.kind}</span>{" "}
                    <strong>{n.title}</strong>
                  </div>
                  {n.message && <div className="muted">{n.message}</div>}
                </div>
                {!n.read && (
                  <button className="btn btn-sm" onClick={() => markOne(n.id)}>
                    Mark read
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
