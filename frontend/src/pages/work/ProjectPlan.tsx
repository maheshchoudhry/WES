import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { workApi, type ProjectPlan as Plan } from "../../api/work";
import { ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

/** AI CEO Analysis — the business analysis and automatic decomposition produced
 * for a Founder intake, with the Founder's plan-approval action. */
export function ProjectPlan() {
  const { id = "" } = useParams();
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const { data, loading, error, reload } = useAsync<Plan>(
    () => workApi.plan(id).then((r) => r.data),
    [id],
  );

  if (loading) return <Loading label="Loading AI CEO analysis…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const a = data.business_analysis;
  const approved = data.project.plan_status === "approved";

  async function act(fn: () => Promise<unknown>, done: string) {
    setBusy(true);
    setMsg(null);
    try {
      await fn();
      setMsg(done);
      reload();
    } catch (err) {
      setMsg(err instanceof Error ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI CEO Analysis — {data.project.name}</h1>
          <p>
            {data.project.code} · Analysed by{" "}
            <strong>{a?.analyst ?? "AI CEO"}</strong> · plan{" "}
            <StatusBadge status={approved ? "active" : "onboarding"} />
          </p>
        </div>
        <div className="quick-actions">
          {!approved && (
            <button
              className="btn"
              disabled={busy}
              onClick={() => act(() => workApi.decompose(id), "Re-analysed by the AI CEO.")}
            >
              Re-run Analysis
            </button>
          )}
          <button
            className="btn btn-primary"
            disabled={busy || approved}
            onClick={() => act(() => workApi.approvePlan(id), "Plan approved.")}
          >
            {approved ? "Plan Approved" : "Approve Plan"}
          </button>
        </div>
      </div>

      {msg && <div className="form-note">{msg}</div>}

      {data.project.business_objective && (
        <SectionCard title="Business Objective">
          <p>{data.project.business_objective}</p>
        </SectionCard>
      )}

      {a && (
        <SectionCard title="Business Analysis (AI CEO)">
          <div className="field">
            <label>Vision</label>
            <p>{a.vision}</p>
          </div>
          <div className="cmd-split">
            <div>
              <div className="cmd-subhead">In Scope</div>
              <ul className="plain-list">
                {a.scope.in_scope.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <div className="cmd-subhead">Out of Scope</div>
              <ul className="plain-list">
                {a.scope.out_of_scope.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
          <div className="field" style={{ marginTop: 12 }}>
            <label>Risks</label>
            <ul className="plain-list">
              {a.risks.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
          <div className="field">
            <label>Architecture Proposal</label>
            <p>{a.architecture_proposal}</p>
          </div>
        </SectionCard>
      )}

      <div className="grid stats" style={{ marginBottom: 16 }}>
        <StatCard label="Epics" value={data.totals.epics} />
        <StatCard label="Sprints" value={data.totals.sprints} />
        <StatCard label="Tasks" value={data.totals.tasks} />
        <StatCard label="Estimated Hours" value={data.totals.estimated_hours} />
      </div>

      <SectionCard
        title="Decomposition"
        action={
          <Link to={`/projects/${id}`} className="btn btn-sm">
            Open Project
          </Link>
        }
      >
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Task</th>
                <th>Title</th>
                <th>Assignee</th>
                <th>Reviewer</th>
                <th>Est. h</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.tasks.map((t) => (
                <tr key={t.task_code}>
                  <td>{t.task_code}</td>
                  <td>{t.title}</td>
                  <td>{t.assignee ?? "—"}</td>
                  <td className="muted">{t.reviewer ?? "—"}</td>
                  <td>{t.estimated_hours ?? "—"}</td>
                  <td>
                    <StatusBadge status={t.status === "backlog" ? "onboarding" : "active"} />
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
