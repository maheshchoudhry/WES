import { Link } from "react-router-dom";

import { aiApi, type AIDeptView, type AISummary } from "../../api/ai";
import { executionApi, type ExecAIDash } from "../../api/execution";
import { workApi, type AIWorkSummary } from "../../api/work";
import { ErrorNotice, Loading } from "../../components/States";
import { QuickActions, SectionCard, StatCard } from "../../components/widgets";
import { useAsync } from "../../hooks/useAsync";

const HEALTH_BADGE: Record<string, "ok" | "warn" | "muted"> = {
  healthy: "ok",
  degraded: "warn",
  at_risk: "warn",
  empty: "muted",
};

async function load(): Promise<{
  summary: AISummary;
  departments: AIDeptView[];
  work: AIWorkSummary;
  exec: ExecAIDash;
}> {
  const [summary, departments, work, exec] = await Promise.all([
    aiApi.summary(),
    aiApi.departmentView(),
    workApi.aiSummary(),
    executionApi.aiDashboard(),
  ]);
  return {
    summary: summary.data,
    departments: departments.data,
    work: work.data,
    exec: exec.data,
  };
}

export function AIDashboard() {
  const { data, loading, error } = useAsync(load, []);
  if (loading) return <Loading label="Loading AI organization…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const { summary, departments, work, exec } = data;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>AI Company</h1>
          <p>The AI organization that runs software development.</p>
        </div>
      </div>

      <div className="grid stats" style={{ marginBottom: 16 }}>
        <StatCard label="AI Employees" value={summary.total_employees} />
        <StatCard label="Departments" value={summary.department_count} />
        <StatCard label="Roles" value={summary.role_count} />
        <StatCard
          label="Organization Health"
          value={<span style={{ textTransform: "capitalize" }}>{summary.organization_health}</span>}
          accent={HEALTH_BADGE[summary.organization_health] ?? "default"}
        />
      </div>

      <div className="dashboard-grid">
        <SectionCard title="Departments">
          <div className="grid dept-grid">
            {departments.map((d) => (
              <Link
                key={d.id}
                to="/ai/departments"
                className="card dept-card"
                style={{ textDecoration: "none" }}
              >
                <div className="dept-card-head">
                  <span className="dept-code">{d.code}</span>
                </div>
                <h3>{d.name}</h3>
                {d.focus && <p className="muted dept-focus">{d.focus}</p>}
                <div className="dept-count">
                  <strong>{d.employee_count}</strong>{" "}
                  {d.employee_count === 1 ? "employee" : "employees"}
                </div>
              </Link>
            ))}
          </div>
        </SectionCard>

        <div className="dashboard-col">
          <SectionCard title="Work">
            <div className="grid stats">
              <StatCard label="Assigned" value={work.assigned_work} />
              <StatCard label="In Progress" value={work.current_tasks} />
              <StatCard label="Completed" value={work.completed_work} accent="ok" />
            </div>
            {Object.keys(work.department_load).length > 0 && (
              <ul className="activity" style={{ marginTop: 12 }}>
                {Object.entries(work.department_load).map(([name, count]) => (
                  <li key={name}>
                    <span className="activity-body">
                      <span className="activity-label">{name} load</span>
                    </span>
                    <strong>{count}</strong>
                  </li>
                ))}
              </ul>
            )}
          </SectionCard>
          <SectionCard title="Execution">
            <div className="grid stats">
              <StatCard label="Execution Queue" value={exec.execution_queue} />
              <StatCard label="Current Work" value={exec.current_work} />
              <StatCard label="Review Queue" value={exec.review_queue} />
            </div>
          </SectionCard>
          <SectionCard title="Explore">
            <QuickActions
              actions={[
                { label: "Directory", to: "/ai/directory" },
                { label: "Workspace", to: "/execution/workspace" },
                { label: "Projects", to: "/projects" },
              ]}
            />
          </SectionCard>
          <SectionCard title="Headcount by Department">
            <ul className="activity">
              {Object.entries(summary.by_department).map(([name, count]) => (
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
    </div>
  );
}
