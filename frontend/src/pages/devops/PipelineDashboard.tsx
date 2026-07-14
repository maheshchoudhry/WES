import { useState } from "react";
import { Link } from "react-router-dom";

import { developmentApi, type DevTask } from "../../api/development";
import { devopsApi, type DevOpsFounderDash, type Pipeline, stageLabel } from "../../api/devops";
import { Empty, ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

const STAGE_STATUS: Record<string, string> = {
  passed: "active",
  failed: "inactive",
  pending: "onboarding",
  skipped: "inactive",
  running: "onboarding",
};

export function PipelineDashboard() {
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<Pipeline | null>(null);
  const { data, loading, error, reload } = useAsync<{
    dash: DevOpsFounderDash;
    approved: DevTask[];
  }>(async () => {
    const [dash, tasks] = await Promise.all([
      devopsApi.founderDashboard(),
      developmentApi.tasks("approved"),
    ]);
    return { dash: dash.data, approved: tasks.data };
  }, []);
  const [taskId, setTaskId] = useState("");

  if (loading) return <Loading label="Loading DevOps…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const d = data.dash;
  const chosen = taskId || data.approved[0]?.id || "";

  async function run() {
    if (!chosen) return alert("No approved task available. Approve a development task first.");
    setBusy(true);
    try {
      const res = await devopsApi.runPipeline(chosen);
      setSelected(res.data);
      reload();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Pipeline failed");
    } finally {
      setBusy(false);
    }
  }

  async function deployProd(p: Pipeline) {
    setBusy(true);
    try {
      await devopsApi.deployProduction(p.id);
      reload();
      setSelected(null);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Deploy failed");
    } finally {
      setBusy(false);
    }
  }

  const latest = selected ?? d.recent_pipelines[0] ?? null;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>CI/CD Pipeline</h1>
          <p>
            From approved implementation to production-ready release: build, test, package, deploy —
            production is Founder-gated.
          </p>
        </div>
      </div>

      <div
        className="card"
        style={{
          display: "flex",
          gap: 12,
          marginBottom: 16,
          alignItems: "center",
          flexWrap: "wrap",
        }}
      >
        <select
          aria-label="Approved task"
          value={chosen}
          onChange={(e) => setTaskId(e.target.value)}
        >
          {data.approved.length === 0 ? (
            <option value="">No approved tasks</option>
          ) : (
            data.approved.map((t) => (
              <option key={t.id} value={t.id}>
                {t.code} — {t.title}
              </option>
            ))
          )}
        </select>
        <button className="btn btn-primary" onClick={run} disabled={busy || !chosen}>
          {busy ? "Running…" : "Run Pipeline"}
        </button>
      </div>

      <div className="grid stats span-all">
        <StatCard label="Pipelines" value={d.total_pipelines} />
        <StatCard
          label="Awaiting Production"
          value={d.awaiting_production}
          accent={d.awaiting_production > 0 ? "warn" : "ok"}
        />
        <StatCard label="Passed" value={d.passed} accent="ok" />
        <StatCard label="Failed" value={d.failed} accent={d.failed > 0 ? "warn" : "ok"} />
      </div>
      <div className="grid stats span-all" style={{ marginTop: 12 }}>
        <StatCard label="Releases" value={d.releases} />
        <StatCard label="Deployments" value={d.deployments} />
        <StatCard label="Prod Deployments" value={d.production_deployments} accent="ok" />
        <StatCard
          label="System Health"
          value={d.system_health ? <StatusBadge status={d.system_health.overall_status} /> : "—"}
          accent={d.system_health?.overall_status === "healthy" ? "ok" : "warn"}
        />
      </div>

      {latest && (
        <SectionCard
          title={`Pipeline ${latest.code} — ${latest.status.replace(/_/g, " ")}`}
          action={
            latest.status === "awaiting_production" ? (
              <button
                className="btn btn-sm btn-primary"
                disabled={busy}
                onClick={() => deployProd(latest)}
              >
                Approve Production Deploy
              </button>
            ) : undefined
          }
        >
          <ul className="activity">
            {latest.stages.map((s, i) => (
              <li key={i}>
                <span className="activity-body">
                  <span className="activity-label">
                    {i + 1}. {stageLabel(s.stage)}
                  </span>
                  <span className="activity-time">{s.detail}</span>
                </span>
                <StatusBadge status={STAGE_STATUS[s.status] ?? "inactive"} />
              </li>
            ))}
          </ul>
        </SectionCard>
      )}

      <SectionCard
        title="Recent Pipelines"
        action={
          <Link to="/devops/deployments" className="btn btn-sm">
            Deployments
          </Link>
        }
      >
        {d.recent_pipelines.length === 0 ? (
          <Empty message="No pipelines yet. Run one above." />
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Status</th>
                  <th>Target</th>
                  <th>Stage</th>
                  <th>Duration</th>
                </tr>
              </thead>
              <tbody>
                {d.recent_pipelines.map((p) => (
                  <tr key={p.id} style={{ cursor: "pointer" }} onClick={() => setSelected(p)}>
                    <td className="muted">{p.code}</td>
                    <td>
                      <StatusBadge
                        status={
                          p.status === "passed"
                            ? "active"
                            : p.status === "failed"
                              ? "inactive"
                              : "onboarding"
                        }
                      />
                    </td>
                    <td>{p.environment_target}</td>
                    <td className="muted">{p.current_stage}</td>
                    <td>{p.duration_ms != null ? `${p.duration_ms}ms` : "—"}</td>
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
