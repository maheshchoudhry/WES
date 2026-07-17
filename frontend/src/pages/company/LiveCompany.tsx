import { Link } from "react-router-dom";

import { companyApi, type LiveCompany as Live } from "../../api/company";
import { ErrorNotice, Loading } from "../../components/States";
import { SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

const STATUS_TONE: Record<string, string> = {
  Coding: "badge-active",
  Testing: "prio-medium",
  Reviewing: "prio-medium",
  Documenting: "prio-low",
  Planning: "prio-low",
  "Repository Analysis": "prio-low",
  "Knowledge Retrieval": "prio-low",
  Packaging: "prio-medium",
  Waiting: "prio-low",
  Blocked: "prio-high",
  Idle: "prio-low",
};

/** Live Company (Parts 8 & 9) — current employee status + company state, all
 * derived from real runtime records. */
export function LiveCompany() {
  const { data, loading, error } = useAsync<Live>(() => companyApi.live().then((r) => r.data), []);
  if (loading) return <Loading label="Loading live company…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;
  const c = data.counts;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Live Company</h1>
          <p>Real-time state of the AI software company — from runtime execution.</p>
        </div>
        <Link to="/company/timeline" className="btn btn-sm">
          Executive Timeline
        </Link>
      </div>

      <SectionCard title="Workforce">
        <div className="grid stats">
          <StatCard label="Working" value={c.working} accent="ok" />
          <StatCard label="Waiting" value={c.waiting} />
          <StatCard label="Blocked" value={c.blocked} accent={c.blocked > 0 ? "warn" : "ok"} />
          <StatCard label="Idle" value={c.idle} accent="muted" />
        </div>
      </SectionCard>

      <SectionCard title="Operations">
        <div className="grid stats">
          <StatCard label="Projects" value={c.projects} />
          <StatCard label="Sprints" value={c.sprints} />
          <StatCard label="Tasks In Progress" value={c.tasks_in_progress} />
          <StatCard label="Queue Length" value={c.queue_length} />
          <StatCard label="Running Jobs" value={c.running_jobs} accent={c.running_jobs > 0 ? "ok" : "muted"} />
          <StatCard label="Pipeline" value={data.pipeline_status ?? "—"} />
          <StatCard label="Provider" value={data.provider} />
          <StatCard label="Repository" value={data.repository ?? "—"} />
        </div>
      </SectionCard>

      <SectionCard title="Live Employee Status">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Role</th>
                <th>Department</th>
                <th>Provider</th>
                <th>Status</th>
                <th>Current Task</th>
              </tr>
            </thead>
            <tbody>
              {data.employees.map((e) => (
                <tr key={e.id}>
                  <td>
                    <Link to={`/ai/employees/${e.id}/workspace`}>{e.name}</Link>
                  </td>
                  <td className="muted">{e.role}</td>
                  <td className="muted">{e.department}</td>
                  <td>
                    <span className="badge prio-low">{e.provider}</span>
                  </td>
                  <td>
                    <span className={`badge ${STATUS_TONE[e.status] ?? "prio-low"}`}>
                      {e.status}
                    </span>
                  </td>
                  <td>{e.current_task ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
