import { Fragment, useMemo, useState } from "react";

import { aiApi } from "../../api/ai";
import { executionApi, type Workspace } from "../../api/execution";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

export function AIWorkspace() {
  const employees = useAsync(() => aiApi.listEmployees().then((r) => r.data), []);
  const [selected, setSelected] = useState<string>("");

  const employeeId = selected || employees.data?.[0]?.id || "";
  const ws = useAsync<Workspace | null>(
    () =>
      employeeId ? executionApi.workspace(employeeId).then((r) => r.data) : Promise.resolve(null),
    [employeeId],
  );

  const options = useMemo(() => employees.data ?? [], [employees.data]);

  if (employees.loading) return <Loading label="Loading workspace…" />;
  if (employees.error) return <ErrorNotice message={employees.error} />;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI Workspace</h1>
          <p>Executable workspace for an AI employee.</p>
        </div>
        <select
          aria-label="Select AI employee"
          value={employeeId}
          onChange={(e) => setSelected(e.target.value)}
        >
          {options.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name} · {o.role_title}
            </option>
          ))}
        </select>
      </div>

      {ws.loading || !ws.data ? (
        <Loading label="Loading workspace…" />
      ) : (
        <WorkspaceView data={ws.data} />
      )}
    </div>
  );
}

function WorkspaceView({ data }: { data: Workspace }) {
  const p = data.performance;
  return (
    <>
      <div className="grid stats" style={{ marginBottom: 16 }}>
        <StatCard label="Queued" value={p.queued} />
        <StatCard label="In Progress" value={p.in_progress} />
        <StatCard label="Completed" value={p.completed} accent="ok" />
        <StatCard
          label="Pending Reviews"
          value={p.pending_reviews}
          accent={p.pending_reviews > 0 ? "warn" : "ok"}
        />
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-col">
          <SectionCard title="Assigned Tasks">
            {data.assigned_tasks.length === 0 ? (
              <p className="muted">None.</p>
            ) : (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Title</th>
                      <th>Priority</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.assigned_tasks.map((t) => (
                      <tr key={t.id}>
                        <td>{t.task_code}</td>
                        <td>{t.title}</td>
                        <td>
                          <span className={`badge prio-${t.priority}`}>{t.priority}</span>
                        </td>
                        <td>
                          <StatusBadge status={t.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </SectionCard>

          <SectionCard title="Execution Queue">
            {data.queue.length === 0 ? (
              <p className="muted">Empty.</p>
            ) : (
              <ul className="activity">
                {data.queue.map((q) => (
                  <li key={q.id}>
                    <span className="activity-body">
                      <span className="activity-label">{q.title}</span>
                      <span className="muted">{q.status}</span>
                    </span>
                    <StatusBadge status={q.status} />
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>

          <SectionCard title="History">
            {data.history.length === 0 ? (
              <p className="muted">No history.</p>
            ) : (
              <ul className="activity">
                {data.history.map((h) => (
                  <li key={h.id}>
                    <span className="activity-body">
                      <span className="activity-label">{h.action}</span>
                      <span className="muted">{h.output ?? ""}</span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>

        <div className="dashboard-col">
          <SectionCard title="Inbox (Handoffs)">
            {data.inbox.length === 0 ? (
              <p className="muted">No pending handoffs.</p>
            ) : (
              <ul className="activity">
                {data.inbox.map((h) => (
                  <li key={h.id}>
                    <span className="activity-body">
                      <span className="activity-label">{h.stage}</span>
                      <span className="muted">{h.status}</span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>

          <SectionCard title="Context">
            {data.context_items.length === 0 ? (
              <p className="muted">No context.</p>
            ) : (
              <dl
                style={{ display: "grid", gridTemplateColumns: "110px 1fr", rowGap: 6, margin: 0 }}
              >
                {data.context_items.map((c) => (
                  <Fragment key={c.key}>
                    <dt className="muted">{c.key}</dt>
                    <dd style={{ margin: 0 }}>{c.value}</dd>
                  </Fragment>
                ))}
              </dl>
            )}
          </SectionCard>

          <SectionCard title="KPIs">
            {data.kpis.length === 0 ? (
              <p className="muted">None.</p>
            ) : (
              <ul className="activity">
                {data.kpis.map((k) => (
                  <li key={k.name}>
                    <span className="activity-body">
                      <span className="activity-label">{k.name}</span>
                    </span>
                    <strong>
                      {k.target ?? "—"}
                      {k.unit ? ` ${k.unit}` : ""}
                    </strong>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>
      </div>
    </>
  );
}
