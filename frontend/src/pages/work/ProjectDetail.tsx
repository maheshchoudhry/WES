import { Link, useParams } from "react-router-dom";

import { workApi, type Milestone, type Project, type Sprint, type WorkItem } from "../../api/work";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { StatusBadge } from "../../components/StatusBadge";
import { useAsync } from "../../hooks/useAsync";

interface Detail {
  project: Project;
  sprints: Sprint[];
  milestones: Milestone[];
  tasks: WorkItem[];
}

export function ProjectDetail() {
  const { id = "" } = useParams();
  const { data, loading, error } = useAsync<Detail>(async () => {
    const [project, sprints, milestones, tasks] = await Promise.all([
      workApi.project(id).then((r) => r.data),
      workApi.sprints(id).then((r) => r.data),
      workApi.milestones(id).then((r) => r.data),
      workApi.tasks({ projectId: id }).then((r) => r.data),
    ]);
    return { project, sprints, milestones, tasks };
  }, [id]);

  if (loading) return <Loading label="Loading project…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const { project, sprints, milestones, tasks } = data;
  const done = tasks.filter((t) => t.status === "done").length;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>
            {project.code} · {project.name}
          </h1>
          <p>
            Owner {project.owner_name ?? "—"} · <StatusBadge status={project.status} /> ·{" "}
            <span className={`badge prio-${project.priority}`}>{project.priority}</span>
          </p>
        </div>
        <Link to="/board" className="btn">
          Open Task Board
        </Link>
      </div>

      <div className="grid stats" style={{ marginBottom: 16 }}>
        <StatCard label="Tasks" value={tasks.length} />
        <StatCard label="Done" value={done} accent="ok" />
        <StatCard label="Sprints" value={sprints.length} />
        <StatCard label="Milestones" value={milestones.length} />
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-col">
          <SectionCard title="Sprints">
            <div className="grid dept-grid">
              {sprints.map((s) => (
                <div className="card dept-card" key={s.id}>
                  <div className="dept-card-head">
                    <span className="dept-code">Sprint {s.sprint_number}</span>
                    <StatusBadge status={s.status} />
                  </div>
                  {s.goal && <p className="muted dept-focus">{s.goal}</p>}
                  <div className="dept-count">
                    <strong>
                      {s.done_count}/{s.task_count}
                    </strong>{" "}
                    done · velocity {s.velocity}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard title="Tasks">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Title</th>
                    <th>Status</th>
                    <th>Assignee</th>
                    <th>Sprint</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((t) => (
                    <tr key={t.id}>
                      <td>{t.task_code}</td>
                      <td>
                        <Link to={`/tasks/${t.id}`}>{t.title}</Link>
                      </td>
                      <td>
                        <StatusBadge status={t.status} />
                      </td>
                      <td>{t.assigned_name ?? "—"}</td>
                      <td>{t.sprint_number ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </SectionCard>
        </div>

        <div className="dashboard-col">
          <SectionCard title="Project">
            <dl style={{ display: "grid", gridTemplateColumns: "110px 1fr", rowGap: 8, margin: 0 }}>
              <dt className="muted">Repository</dt>
              <dd style={{ margin: 0 }}>{project.repository ?? "—"}</dd>
              <dt className="muted">Tech Stack</dt>
              <dd style={{ margin: 0 }}>{project.tech_stack ?? "—"}</dd>
              <dt className="muted">Version</dt>
              <dd style={{ margin: 0 }}>v{project.version}</dd>
            </dl>
          </SectionCard>

          <SectionCard title="Milestones">
            {milestones.length === 0 ? (
              <p className="muted">None.</p>
            ) : (
              <ul className="activity">
                {milestones.map((m) => (
                  <li key={m.id}>
                    <span className="activity-body">
                      <span className="activity-label">{m.name}</span>
                      <span className="muted">
                        {m.status} · due {m.due_date ?? "—"}
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
