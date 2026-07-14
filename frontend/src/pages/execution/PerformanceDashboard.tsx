import { executionApi, type ExecAIDash, type ExecFounderDash } from "../../api/execution";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

async function load(): Promise<{ founder: ExecFounderDash; ai: ExecAIDash }> {
  const [founder, ai] = await Promise.all([
    executionApi.founderDashboard(),
    executionApi.aiDashboard(),
  ]);
  return { founder: founder.data, ai: ai.data };
}

export function PerformanceDashboard() {
  const { data, loading, error } = useAsync(load, []);
  if (loading) return <Loading label="Loading performance…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const { founder, ai } = data;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Performance Dashboard</h1>
          <p>Execution performance across the AI organization.</p>
        </div>
      </div>

      <div className="grid stats" style={{ marginBottom: 16 }}>
        <StatCard label="Work Queue" value={founder.ai_work_queue} />
        <StatCard label="In Progress" value={founder.in_progress} />
        <StatCard
          label="Pending Reviews"
          value={founder.pending_reviews}
          accent={founder.pending_reviews > 0 ? "warn" : "ok"}
        />
        <StatCard label="Completed" value={founder.completed_work} accent="ok" />
      </div>

      <div className="dashboard-grid">
        <SectionCard title="Organization Performance">
          <dl style={{ display: "grid", gridTemplateColumns: "180px 1fr", rowGap: 8, margin: 0 }}>
            <dt className="muted">Total executions</dt>
            <dd style={{ margin: 0 }}>{founder.organization_performance.total_executions}</dd>
            <dt className="muted">Handoffs</dt>
            <dd style={{ margin: 0 }}>{founder.organization_performance.handoffs}</dd>
            <dt className="muted">Avg completion</dt>
            <dd style={{ margin: 0 }}>
              {founder.avg_completion_seconds != null
                ? `${Math.round(founder.avg_completion_seconds / 60)} min`
                : "—"}
            </dd>
          </dl>
        </SectionCard>

        <SectionCard title="Work by AI Employee">
          <ul className="activity">
            {Object.entries(ai.work_by_employee).map(([name, count]) => (
              <li key={name}>
                <span className="activity-body">
                  <span className="activity-label">{name}</span>
                </span>
                <strong>{count}</strong>
              </li>
            ))}
          </ul>
        </SectionCard>
      </div>
    </div>
  );
}
