import { Link } from "react-router-dom";

import { orchestrationApi, type PlatformDash } from "../../api/orchestration";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function ProviderDashboard() {
  const { data, loading, error } = useAsync<PlatformDash>(
    () => orchestrationApi.platformDashboard().then((r) => r.data),
    [],
  );
  if (loading) return <Loading label="Loading provider platform…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Provider Dashboard</h1>
          <p>Live provider status, usage, cost, and latency across the platform.</p>
        </div>
        <Link to="/settings/providers" className="btn">
          Provider Settings
        </Link>
      </div>

      <div className="grid stats span-all">
        <StatCard label="Completed" value={data.completed_executions} accent="ok" />
        <StatCard
          label="Failed"
          value={data.failed_executions}
          accent={data.failed_executions > 0 ? "warn" : "ok"}
        />
        <StatCard label="Token Usage" value={data.token_usage} />
        <StatCard label="Est. Cost" value={`$${data.estimated_cost.toFixed(4)}`} />
      </div>

      <SectionCard title="Providers">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Provider</th>
                <th>Health</th>
                <th>Active Model</th>
                <th>Key</th>
                <th>Priority</th>
                <th>Default</th>
              </tr>
            </thead>
            <tbody>
              {data.providers.map((p) => (
                <tr key={p.name}>
                  <td>{p.name}</td>
                  <td>
                    <StatusBadge status={p.health} />
                  </td>
                  <td className="muted">{p.active_model ?? "—"}</td>
                  <td>{p.has_secret ? "✓" : p.name === "mock" ? "n/a" : "—"}</td>
                  <td>{p.priority}</td>
                  <td>{p.is_default ? "★" : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard title="Provider Metrics">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Provider</th>
                <th>Avg Latency</th>
                <th>Errors</th>
                <th>Tokens</th>
                <th>Cost</th>
              </tr>
            </thead>
            <tbody>
              {data.metrics.map((m) => (
                <tr key={m.provider}>
                  <td>{m.provider}</td>
                  <td>{m.avg_latency_ms != null ? `${m.avg_latency_ms}ms` : "—"}</td>
                  <td>{m.errors}</td>
                  <td>{m.tokens}</td>
                  <td>${m.cost.toFixed(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>

      <SectionCard title="Cost by Provider">
        <div className="quick-actions">
          {data.cost_by_provider.map((c) => (
            <span key={c.key ?? c.label} className="badge prio-low">
              {c.label}: {c.tokens} tok · ${c.cost.toFixed(4)}
            </span>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Recent Events">
        {data.recent_events.length === 0 ? (
          <p className="muted">No events yet.</p>
        ) : (
          <ul className="activity">
            {data.recent_events.map((e) => (
              <li key={e.id}>
                <span className="activity-body">
                  <span className="activity-label">{e.event_type}</span>
                  <span className="activity-time">{e.detail}</span>
                </span>
                <span className={`badge ${e.severity === "warning" ? "prio-high" : "prio-low"}`}>
                  {e.provider ?? "—"}
                </span>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}
