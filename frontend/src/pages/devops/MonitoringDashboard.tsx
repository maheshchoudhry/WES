import { devopsApi, type MonitoringEvent, type SystemHealthSnapshot } from "../../api/devops";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function MonitoringDashboard() {
  const { data, loading, error, reload } = useAsync<{
    health: SystemHealthSnapshot | null;
    events: MonitoringEvent[];
  }>(async () => {
    const [health, events] = await Promise.all([devopsApi.health(), devopsApi.events()]);
    return { health: health.data, events: events.data };
  }, []);

  async function snapshot() {
    await devopsApi.snapshot();
    reload();
  }

  if (loading) return <Loading label="Loading monitoring…" />;
  if (error) return <ErrorNotice message={error} />;
  const h = data?.health;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Monitoring Dashboard</h1>
          <p>Real system, application, database, and provider health.</p>
        </div>
        <button className="btn btn-primary" onClick={snapshot}>
          Capture Snapshot
        </button>
      </div>

      {h && (
        <>
          <div className="grid stats span-all">
            <StatCard
              label="Overall"
              value={<StatusBadge status={h.overall_status} />}
              accent={h.overall_status === "healthy" ? "ok" : "warn"}
            />
            <StatCard label="CPU" value={`${h.cpu_pct}%`} accent={h.cpu_pct > 85 ? "warn" : "ok"} />
            <StatCard
              label="Memory"
              value={`${h.memory_pct}%`}
              accent={h.memory_pct > 85 ? "warn" : "ok"}
            />
            <StatCard
              label="Disk"
              value={`${h.disk_pct}%`}
              accent={h.disk_pct > 90 ? "warn" : "ok"}
            />
          </div>
          <div className="grid stats span-all" style={{ marginTop: 12 }}>
            <StatCard
              label="Database"
              value={<StatusBadge status={h.db_status === "healthy" ? "active" : "inactive"} />}
            />
            <StatCard
              label="Providers"
              value={
                <StatusBadge status={h.provider_status === "healthy" ? "active" : "onboarding"} />
              }
            />
            <StatCard label="Queue Depth" value={h.queue_depth} />
            <StatCard label="Response Time" value={`${h.response_time_ms}ms`} />
          </div>
        </>
      )}

      <SectionCard title="Monitoring Events">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Category</th>
                <th>Metric</th>
                <th>Value</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {(data?.events ?? []).map((e, i) => (
                <tr key={i}>
                  <td>{e.category}</td>
                  <td className="muted">{e.metric}</td>
                  <td>
                    {e.value}
                    {e.unit ?? ""}
                  </td>
                  <td>
                    <StatusBadge status={e.status === "healthy" ? "active" : "onboarding"} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
