import { Link } from "react-router-dom";

import { orchestrationApi, type PlatformDash, type Run } from "../../api/orchestration";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function ExecutionMonitor() {
  const { data, loading, error, reload } = useAsync<{
    runs: Run[];
    dash: PlatformDash;
  }>(async () => {
    const [runs, dash] = await Promise.all([
      orchestrationApi.runs(),
      orchestrationApi.platformDashboard(),
    ]);
    return { runs: runs.data, dash: dash.data };
  }, []);
  if (loading) return <Loading label="Loading executions…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Execution Monitor</h1>
          <p>Live executions across all providers, with latency and status.</p>
        </div>
        <button className="btn" onClick={reload}>
          Refresh
        </button>
      </div>

      <div className="grid stats span-all">
        <StatCard label="Running" value={data.dash.running_executions} />
        <StatCard label="Completed" value={data.dash.completed_executions} accent="ok" />
        <StatCard
          label="Failed"
          value={data.dash.failed_executions}
          accent={data.dash.failed_executions > 0 ? "warn" : "ok"}
        />
        <StatCard
          label="Avg Latency"
          value={data.dash.avg_latency_ms != null ? `${data.dash.avg_latency_ms}ms` : "—"}
        />
      </div>

      <SectionCard title="Executions">
        {data.runs.length === 0 ? (
          <Empty message="No executions yet." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Employee</th>
                  <th>Provider</th>
                  <th>Model</th>
                  <th>Status</th>
                  <th>Latency</th>
                  <th>Output</th>
                </tr>
              </thead>
              <tbody>
                {data.runs.map((r) => (
                  <tr key={r.id}>
                    <td>{r.ai_employee_name}</td>
                    <td>{r.provider_name}</td>
                    <td className="muted">{r.model}</td>
                    <td>
                      <StatusBadge status={r.status} />
                    </td>
                    <td>{r.duration_ms != null ? `${r.duration_ms}ms` : "—"}</td>
                    <td className="muted">
                      {r.thread_id ? (
                        <Link to={`/orchestration/threads/${r.thread_id}`}>
                          {(r.output ?? r.error ?? "").slice(0, 50)}
                        </Link>
                      ) : (
                        (r.output ?? r.error ?? "").slice(0, 50)
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
