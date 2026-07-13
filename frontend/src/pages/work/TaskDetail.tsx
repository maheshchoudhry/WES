import { Link, useParams } from "react-router-dom";

import { workApi, type ActivityEntry, type WorkItem } from "../../api/work";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

interface Detail {
  task: WorkItem;
  activity: ActivityEntry[];
}

export function TaskDetail() {
  const { id = "" } = useParams();
  const { data, loading, error, reload } = useAsync<Detail>(async () => {
    const [task, activity] = await Promise.all([
      workApi.task(id).then((r) => r.data),
      workApi.activity({ workItemId: id }).then((r) => r.data),
    ]);
    return { task, activity };
  }, [id]);

  if (loading) return <Loading label="Loading task…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const t = data.task;

  async function setStatus(status: string) {
    await workApi.updateTask(t.id, { status });
    reload();
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>
            {t.task_code} · {t.title}
          </h1>
          <p>
            <StatusBadge status={t.status} /> ·{" "}
            <span className={`badge prio-${t.priority}`}>{t.priority}</span> · {t.project_code}
          </p>
        </div>
        <Link to="/board" className="btn">
          Board
        </Link>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-col">
          <SectionCard title="Details">
            <dl style={{ display: "grid", gridTemplateColumns: "150px 1fr", rowGap: 8, margin: 0 }}>
              <dt className="muted">Description</dt>
              <dd style={{ margin: 0 }}>{t.description ?? "—"}</dd>
              <dt className="muted">Acceptance Criteria</dt>
              <dd style={{ margin: 0 }}>{t.acceptance_criteria ?? "—"}</dd>
              <dt className="muted">Assignee</dt>
              <dd style={{ margin: 0 }}>{t.assigned_name ?? "Unassigned"}</dd>
              <dt className="muted">Reviewer</dt>
              <dd style={{ margin: 0 }}>{t.reviewer_name ?? "—"}</dd>
              <dt className="muted">Sprint</dt>
              <dd style={{ margin: 0 }}>{t.sprint_number ?? "—"}</dd>
              <dt className="muted">Estimate</dt>
              <dd style={{ margin: 0 }}>{t.estimated_hours ?? "—"} h</dd>
            </dl>
          </SectionCard>
        </div>

        <div className="dashboard-col">
          <SectionCard title="Status">
            <div className="field">
              <label htmlFor="t-status">Change status</label>
              <select id="t-status" value={t.status} onChange={(e) => setStatus(e.target.value)}>
                {[
                  "backlog",
                  "planned",
                  "assigned",
                  "in_progress",
                  "review",
                  "testing",
                  "done",
                  "blocked",
                  "archived",
                ].map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </SectionCard>

          <SectionCard title="Activity">
            {data.activity.length === 0 ? (
              <p className="muted">No activity yet.</p>
            ) : (
              <ul className="activity">
                {data.activity.map((a) => (
                  <li key={a.id}>
                    <span className="activity-body">
                      <span className="activity-label">{a.action}</span>
                      <span className="muted">
                        {a.actor}
                        {a.detail ? ` · ${a.detail}` : ""}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
