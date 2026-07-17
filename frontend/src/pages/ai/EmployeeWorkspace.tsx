import { useParams } from "react-router-dom";

import { companyApi, type EmployeeWorkspace as WS } from "../../api/company";
import { ErrorNotice, Loading } from "../../components/States";
import { StatusBadge } from "../../components/StatusBadge";
import { SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

/** AI Employee Workspace (Parts 1,2,3,5,6) — profile, current context, inbox,
 * tasks, decision timeline and handoff history, all from real runtime records. */
export function EmployeeWorkspace() {
  const { id = "" } = useParams();
  const { data, loading, error } = useAsync<WS>(
    () => companyApi.workspace(id).then((r) => r.data),
    [id],
  );
  if (loading) return <Loading label="Loading workspace…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const { profile: p, current: cur, performance: perf } = data;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>{p.name} — Workspace</h1>
          <p>
            {p.role} · {p.department} · <span className="badge prio-low">{p.provider}</span>
          </p>
        </div>
        <span className="badge badge-active">{p.status}</span>
      </div>

      <div className="cmd-header card">
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Authority</span>
          <span className="cmd-meta-value" style={{ textTransform: "capitalize" }}>
            {p.authority}
          </span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Current Project</span>
          <span className="cmd-meta-value">{cur.project ?? "—"}</span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Current Sprint</span>
          <span className="cmd-meta-value">{cur.sprint ?? "—"}</span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Current Task</span>
          <span className="cmd-meta-value">{cur.task ?? "—"}</span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Branch</span>
          <span className="cmd-meta-value">{cur.branch ?? "—"}</span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Repository</span>
          <span className="cmd-meta-value">{cur.repository ?? "—"}</span>
        </div>
      </div>

      <div className="grid stats" style={{ marginBottom: 16 }}>
        <StatCard label="Assigned" value={perf.assigned} />
        <StatCard label="In Progress" value={perf.in_progress} accent="ok" />
        <StatCard label="Done" value={perf.done} />
        <StatCard label="Stages Performed" value={perf.stages_performed} />
      </div>

      <div className="cmd-layout">
        <div className="cmd-main">
          <SectionCard title="Inbox">
            {data.inbox.length === 0 ? (
              <p className="muted">No tasks in the inbox.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Task</th>
                      <th>Title</th>
                      <th>Project</th>
                      <th>Sender</th>
                      <th>Priority</th>
                      <th>Est. h</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.inbox.map((t) => (
                      <tr key={t.task_code}>
                        <td>{t.task_code}</td>
                        <td>{t.title}</td>
                        <td className="muted">{t.project ?? "—"}</td>
                        <td className="muted">{t.sender ?? "—"}</td>
                        <td>
                          <span className="badge prio-low">{t.priority}</span>
                        </td>
                        <td>{t.estimated_hours ?? "—"}</td>
                        <td>
                          <StatusBadge status={t.status === "done" ? "active" : "onboarding"} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SectionCard>

          <SectionCard title="Decision Timeline">
            {data.decisions.length === 0 ? (
              <p className="muted">No decisions recorded yet.</p>
            ) : (
              <div className="timeline">
                {data.decisions.map((d, i) => (
                  <div key={i} className="timeline-row" data-testid="decision-row">
                    <span className="timeline-dot" aria-hidden="true" />
                    <div className="timeline-body">
                      <div className="timeline-head">
                        <span className="badge prio-medium">{d.decision}</span>
                        {d.provider && <span className="badge prio-low">{d.provider}</span>}
                      </div>
                      {d.reason && <div className="muted">{d.reason}</div>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </div>

        <aside className="cmd-aside">
          <SectionCard title="Tasks">
            {Object.entries(data.tasks).map(([bucket, codes]) => (
              <div key={bucket} className="mini-item">
                <span style={{ textTransform: "capitalize" }}>{bucket.replace("_", " ")}</span>
                <span className="badge prio-low">{codes.length}</span>
              </div>
            ))}
          </SectionCard>

          <SectionCard title="Handoff History">
            {data.handoffs.length === 0 ? (
              <p className="muted">No handoffs yet.</p>
            ) : (
              <div className="mini-list">
                {data.handoffs.map((h, i) => (
                  <div key={i} className="convo-item" data-testid="handoff-row">
                    <div className="convo-head">
                      <strong>{h.from}</strong> → <strong>{h.to}</strong>
                    </div>
                    <div className="muted">{h.reason}</div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Long-Term Memory">
            {(data.memory ?? []).length === 0 ? (
              <p className="muted">No memories yet.</p>
            ) : (
              <div className="mini-list">
                {data.memory.map((m) => (
                  <div key={m.id} className="convo-item" data-testid="memory-row">
                    <div className="convo-head">
                      <span className="badge prio-low">{m.kind}</span>
                    </div>
                    <div className="muted">{m.summary}</div>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>
        </aside>
      </div>
    </div>
  );
}
