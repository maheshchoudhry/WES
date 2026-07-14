import { qualityApi, type QualityRule } from "../../api/quality";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";
import { useQualityReport } from "./useQualityReport";

export function QualityGateDashboard() {
  const { dash, report, loading, error } = useQualityReport();
  const { data: rules } = useAsync<QualityRule[]>(() => qualityApi.rules().then((r) => r.data), []);

  if (loading) return <Loading label="Loading quality gates…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!dash) return <Empty message="No quality gate runs yet." />;
  const gate = report?.gate;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Quality Gate Dashboard</h1>
          <p>
            The final engineering-validation layer. No implementation reaches Founder approval until
            all mandatory gates pass.
          </p>
        </div>
      </div>

      <div className="grid stats span-all">
        <StatCard label="Gate Runs" value={dash.total_gate_runs} />
        <StatCard label="Approval-Eligible" value={dash.approval_eligible} accent="ok" />
        <StatCard label="Blocked" value={dash.blocked} accent={dash.blocked > 0 ? "warn" : "ok"} />
        <StatCard
          label="Open Critical"
          value={dash.open_critical}
          accent={dash.open_critical > 0 ? "warn" : "ok"}
        />
      </div>
      <div className="grid stats span-all" style={{ marginTop: 12 }}>
        <StatCard label="Avg Review Score" value={dash.avg_review_score.toFixed(0)} accent="ok" />
        <StatCard label="Avg Security Score" value={dash.avg_security_score.toFixed(0)} />
        <StatCard label="Avg Performance" value={dash.avg_performance_score.toFixed(0)} />
        <StatCard label="Release Ready" value={dash.release_ready} accent="ok" />
      </div>

      {gate && (
        <SectionCard title={`Latest Gate — ${gate.approval_eligible ? "Passed" : "Blocked"}`}>
          <div className="grid stats" style={{ marginBottom: 12 }}>
            <StatCard label="Overall" value={gate.overall_score.toFixed(0)} accent="ok" />
            <StatCard label="Architecture" value={gate.architecture_score.toFixed(0)} />
            <StatCard label="Security" value={gate.security_score.toFixed(0)} />
            <StatCard label="Tests" value={`${gate.tests_passed_pct.toFixed(0)}%`} accent="ok" />
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Gate</th>
                  <th>Value</th>
                  <th>Threshold</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {gate.gates.map((g) => (
                  <tr key={g.code}>
                    <td>{g.name}</td>
                    <td>{g.value ?? "—"}</td>
                    <td className="muted">{g.threshold ?? "—"}</td>
                    <td>
                      <StatusBadge status={g.passed ? "active" : "inactive"} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      )}

      <SectionCard title="Mandatory Quality Rules">
        <div className="quick-actions">
          {(rules ?? []).map((r) => (
            <span key={r.code} className="badge prio-medium">
              {r.name}
            </span>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Recent Gate Runs">
        {dash.recent.length === 0 ? (
          <Empty message="No gate runs yet." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Overall</th>
                  <th>Security</th>
                  <th>Critical</th>
                  <th>Eligible</th>
                </tr>
              </thead>
              <tbody>
                {dash.recent.map((g) => (
                  <tr key={g.task_id}>
                    <td className="muted">{g.task_id.slice(0, 8)}</td>
                    <td>{g.overall_score.toFixed(0)}</td>
                    <td>{g.security_score.toFixed(0)}</td>
                    <td>{g.critical_count}</td>
                    <td>
                      <StatusBadge status={g.approval_eligible ? "active" : "inactive"} />
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
