import { Link } from "react-router-dom";

import { aiApi, type AISummary } from "../api/ai";
import { dashboardApi } from "../api/dashboard";
import { executionApi, type ExecFounderDash } from "../api/execution";
import { knowledgeApi, type KnowledgeFounderDash } from "../api/knowledge";
import { orchestrationApi, type OrchFounderDash } from "../api/orchestration";
import { repositoryApi, type Repository } from "../api/repository";
import { developmentApi, type DevFounderDash } from "../api/development";
import { workApi, type FounderWorkSummary } from "../api/work";
import type {
  ActivityItem,
  DashboardStats,
  DepartmentStat,
  EmployeeDirectoryItem,
  SystemHealth,
} from "../api/dashboard";
import { Empty, ErrorNotice, Loading } from "../components/States";
import { StatusBadge } from "../components/StatusBadge";
import {
  ActivityFeed,
  CompanyHealth,
  DepartmentCard,
  OrgSnapshot,
  QuickActions,
  SectionCard,
  StatCard,
} from "../components/widgets";
import { useAsync } from "../hooks/useAsync";

interface DashboardData {
  stats: DashboardStats;
  departments: DepartmentStat[];
  employees: EmployeeDirectoryItem[];
  activity: ActivityItem[];
  health: SystemHealth;
  ai: AISummary;
  work: FounderWorkSummary;
  exec: ExecFounderDash;
  orch: OrchFounderDash;
  knowledge: KnowledgeFounderDash;
  repository: Repository | null;
  development: DevFounderDash;
}

async function loadDashboard(): Promise<DashboardData> {
  const [
    stats,
    departments,
    employees,
    activity,
    health,
    ai,
    work,
    exec,
    orch,
    knowledge,
    repository,
    development,
  ] = await Promise.all([
    dashboardApi.stats(),
    dashboardApi.departments(),
    dashboardApi.employees(),
    dashboardApi.activity(8),
    dashboardApi.health(),
    aiApi.summary(),
    workApi.founderSummary(),
    executionApi.founderDashboard(),
    orchestrationApi.founderDashboard(),
    knowledgeApi.founderDashboard(),
    repositoryApi.list().then((r) => ({ data: r.data[0] ?? null })),
    developmentApi.founderDashboard(),
  ]);
  return {
    stats: stats.data,
    departments: departments.data,
    employees: employees.data,
    activity: activity.data,
    health: health.data,
    ai: ai.data,
    work: work.data,
    exec: exec.data,
    orch: orch.data,
    knowledge: knowledge.data,
    repository: repository.data,
    development: development.data,
  };
}

export function Dashboard() {
  const { data, loading, error } = useAsync(loadDashboard, []);

  if (loading) return <Loading label="Loading dashboard…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const {
    stats,
    departments,
    employees,
    activity,
    health,
    ai,
    work,
    exec,
    orch,
    knowledge,
    repository,
    development,
  } = data;
  const company = stats.company;
  const aiHealthAccent: "ok" | "warn" | "muted" =
    ai.organization_health === "healthy"
      ? "ok"
      : ai.organization_health === "empty"
        ? "muted"
        : "warn";

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Founder Dashboard</h1>
          <p>{company ? company.name : "WES OS"} — current state of the company.</p>
        </div>
        {company && <StatusBadge status={company.status} />}
      </div>

      {!company ? (
        <Empty message="No company exists yet. Create one from the Company page to populate the dashboard." />
      ) : (
        <div className="dashboard-grid">
          {/* Statistics cards */}
          <div className="grid stats span-all">
            <StatCard label="Departments" value={stats.totals.departments} />
            <StatCard label="Employees" value={stats.totals.employees} />
            <StatCard
              label="Active Projects"
              value={stats.totals.active_projects}
              hint="Projects arrive in a future sprint"
              accent="muted"
            />
            <StatCard
              label="Active Employees"
              value={stats.employees_by_status.active ?? 0}
              accent="ok"
            />
          </div>

          {/* AI Organization summary */}
          <div className="span-all">
            <SectionCard
              title="AI Organization"
              action={
                <Link to="/ai" className="btn btn-sm">
                  Open AI Company
                </Link>
              }
            >
              <div className="grid stats">
                <StatCard label="AI Employees" value={ai.total_employees} />
                <StatCard label="AI Departments" value={ai.department_count} />
                <StatCard label="AI Roles" value={ai.role_count} />
                <StatCard
                  label="Organization Health"
                  value={
                    <span style={{ textTransform: "capitalize" }}>{ai.organization_health}</span>
                  }
                  accent={aiHealthAccent}
                />
              </div>
            </SectionCard>
          </div>

          {/* Work summary */}
          <div className="span-all">
            <SectionCard
              title="Work Management"
              action={
                <Link to="/projects" className="btn btn-sm">
                  Projects
                </Link>
              }
            >
              <div className="grid stats">
                <StatCard label="Projects" value={work.total_projects} />
                <StatCard label="Tasks" value={work.total_tasks} />
                <StatCard
                  label="Blocked"
                  value={work.blocked_tasks}
                  accent={work.blocked_tasks > 0 ? "warn" : "ok"}
                />
                <StatCard label="Velocity" value={work.velocity} hint="completed sprints" />
              </div>
            </SectionCard>
          </div>

          {/* Execution summary */}
          <div className="span-all">
            <SectionCard
              title="AI Execution"
              action={
                <Link to="/execution/performance" className="btn btn-sm">
                  Performance
                </Link>
              }
            >
              <div className="grid stats">
                <StatCard label="Work Queue" value={exec.ai_work_queue} />
                <StatCard label="In Progress" value={exec.in_progress} />
                <StatCard
                  label="Pending Reviews"
                  value={exec.pending_reviews}
                  accent={exec.pending_reviews > 0 ? "warn" : "ok"}
                />
                <StatCard label="Completed" value={exec.completed_work} accent="ok" />
              </div>
            </SectionCard>
          </div>

          {/* Orchestration summary */}
          <div className="span-all">
            <SectionCard
              title="AI Orchestration"
              action={
                <Link to="/settings/providers" className="btn btn-sm">
                  Providers
                </Link>
              }
            >
              <div className="grid stats">
                <StatCard label="Completed Runs" value={orch.completed_executions} accent="ok" />
                <StatCard
                  label="Failed Runs"
                  value={orch.failed_executions}
                  accent={orch.failed_executions > 0 ? "warn" : "ok"}
                />
                <StatCard label="Token Usage" value={orch.token_usage} />
                <StatCard
                  label="Est. Cost"
                  value={`$${orch.estimated_cost.toFixed(4)}`}
                  hint="mock is free"
                />
              </div>
              <div className="quick-actions" style={{ marginTop: 12 }}>
                {orch.providers.map((p) => (
                  <span key={p.name} className="badge prio-medium">
                    {p.name}: {p.health}
                    {p.is_default ? " ★" : ""}
                  </span>
                ))}
              </div>
            </SectionCard>
          </div>

          {/* Autonomous development summary */}
          <div className="span-all">
            <SectionCard
              title="Autonomous Development"
              action={
                <Link to="/development" className="btn btn-sm">
                  Development
                </Link>
              }
            >
              <div className="grid stats">
                <StatCard label="Running" value={development.running} />
                <StatCard label="Completed" value={development.completed} accent="ok" />
                <StatCard
                  label="Pending Approvals"
                  value={development.pending_approvals}
                  accent={development.pending_approvals > 0 ? "warn" : "ok"}
                />
                <StatCard label="Open PRs" value={development.open_pull_requests} />
              </div>
            </SectionCard>
          </div>

          {/* Repository intelligence summary */}
          {repository && repository.metrics && (
            <div className="span-all">
              <SectionCard
                title="Repository Intelligence"
                action={
                  <Link to="/repository" className="btn btn-sm">
                    Repository
                  </Link>
                }
              >
                <div className="grid stats">
                  <StatCard label="Files" value={repository.metrics.file_count} />
                  <StatCard label="Symbols" value={repository.metrics.symbol_count} />
                  <StatCard label="Routes" value={repository.metrics.route_count} />
                  <StatCard
                    label="Health"
                    value={repository.metrics.health_score.toFixed(0)}
                    accent={repository.metrics.health_score >= 60 ? "ok" : "warn"}
                    hint={repository.primary_language ?? ""}
                  />
                </div>
              </SectionCard>
            </div>
          )}

          {/* Knowledge summary */}
          <div className="span-all">
            <SectionCard
              title="Organizational Knowledge"
              action={
                <Link to="/knowledge" className="btn btn-sm">
                  Knowledge Base
                </Link>
              }
            >
              <div className="grid stats">
                <StatCard label="Documents" value={knowledge.documents} />
                <StatCard label="Categories" value={knowledge.categories} />
                <StatCard
                  label="Pending Reviews"
                  value={knowledge.pending_reviews}
                  accent={knowledge.pending_reviews > 0 ? "warn" : "ok"}
                />
                <StatCard
                  label="Knowledge Health"
                  value={
                    <span style={{ textTransform: "capitalize" }}>
                      {knowledge.knowledge_health}
                    </span>
                  }
                  accent={
                    knowledge.knowledge_health === "healthy"
                      ? "ok"
                      : knowledge.knowledge_health === "empty"
                        ? "muted"
                        : "warn"
                  }
                  hint={`${knowledge.statistics.retrievals} AI retrievals`}
                />
              </div>
            </SectionCard>
          </div>

          {/* Left column */}
          <div className="dashboard-col">
            <SectionCard title="Department Overview">
              {departments.length === 0 ? (
                <p className="muted">No departments yet.</p>
              ) : (
                <div className="grid dept-grid">
                  {departments.map((d) => (
                    <DepartmentCard key={d.id} dept={d} />
                  ))}
                </div>
              )}
            </SectionCard>

            <SectionCard title="Employee Workspace">
              {employees.length === 0 ? (
                <p className="muted">No employees yet.</p>
              ) : (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Position</th>
                        <th>Department</th>
                        <th>Manager</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {employees.map((e) => (
                        <tr key={e.id}>
                          <td>{e.employee_code}</td>
                          <td>{e.full_name}</td>
                          <td className="muted">{e.position}</td>
                          <td>{e.department_name ?? "—"}</td>
                          <td>{e.manager_name ?? "—"}</td>
                          <td>
                            <StatusBadge status={e.status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </SectionCard>
          </div>

          {/* Right column */}
          <div className="dashboard-col">
            <SectionCard title="Quick Actions">
              <QuickActions
                actions={[
                  { label: "Company", to: "/company" },
                  { label: "Departments", to: "/departments" },
                  { label: "Employees", to: "/employees" },
                  { label: "Projects", to: "/projects", disabled: true },
                ]}
              />
            </SectionCard>

            <SectionCard title="Company Health">
              <CompanyHealth health={health} />
            </SectionCard>

            <SectionCard title="Organization Snapshot">
              <OrgSnapshot employees={employees} />
            </SectionCard>

            <SectionCard title="Recent Activity">
              <ActivityFeed items={activity} />
            </SectionCard>
          </div>
        </div>
      )}
    </div>
  );
}
