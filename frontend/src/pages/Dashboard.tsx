import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { aiApi, type AISummary } from "../api/ai";
import { dashboardApi } from "../api/dashboard";
import { executionApi, type ExecFounderDash } from "../api/execution";
import { knowledgeApi, type KnowledgeFounderDash } from "../api/knowledge";
import { orchestrationApi, type OrchFounderDash } from "../api/orchestration";
import { repositoryApi, type Repository } from "../api/repository";
import { developmentApi, type DevFounderDash } from "../api/development";
import { qualityApi, type QualityFounderDash } from "../api/quality";
import { devopsApi, type DevOpsFounderDash } from "../api/devops";
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
  quality: QualityFounderDash;
  devops: DevOpsFounderDash;
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
    quality,
    devops,
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
    qualityApi.founderDashboard(),
    devopsApi.founderDashboard(),
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
    quality: quality.data,
    devops: devops.data,
  };
}

// -- helpers -----------------------------------------------------------------

type Tone = "ok" | "warn" | "muted";

function tone(status: string | undefined | null): Tone {
  const s = (status ?? "").toLowerCase();
  if (["healthy", "ok", "active", "connected", "passed", "ready", "present"].includes(s))
    return "ok";
  if (["empty", "none", "unknown", "n/a", ""].includes(s)) return "muted";
  return "warn";
}

function HealthPill({ label, status }: { label: string; status: string }) {
  const t = tone(status);
  return (
    <div className="health-pill">
      <span className={`health-dot ${t}`} aria-hidden="true" />
      <span className="health-pill-label">{label}</span>
      <span className={`health-pill-status ${t}`}>{status || "—"}</span>
    </div>
  );
}

function useClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

// -- page --------------------------------------------------------------------

export function Dashboard() {
  const { data, loading, error } = useAsync(loadDashboard, []);
  const now = useClock();

  if (loading) return <Loading label="Loading command center…" />;
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
    quality,
    devops,
  } = data;
  const company = stats.company;
  const provider = orch.providers.find((p) => p.is_default) ?? orch.providers[0];
  const sys = devops.system_health;
  const companyStatus =
    health.api === "ok" && health.database === "connected" ? "healthy" : "degraded";
  const repoStatus = repository?.metrics
    ? repository.metrics.health_score >= 60
      ? "healthy"
      : "degraded"
    : "empty";
  const systemStatus = sys?.overall_status ?? (health.api === "ok" ? "healthy" : "degraded");

  if (!company) {
    return (
      <div>
        <div className="page-header">
          <div>
            <h1>Founder Dashboard</h1>
            <p>WES OS — command center.</p>
          </div>
        </div>
        <Empty message="No company exists yet. Create one from the Company page to populate the command center." />
      </div>
    );
  }

  return (
    <div className="cmd">
      {/* Command header */}
      <div className="page-header">
        <div>
          <h1>Founder Dashboard</h1>
          <p>{company.name} — AI Software Company Command Center</p>
        </div>
        <StatusBadge status={company.status} />
      </div>

      <div className="cmd-header card">
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Company</span>
          <span className="cmd-meta-value">{company.name}</span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Environment</span>
          <span className="cmd-meta-value" style={{ textTransform: "capitalize" }}>
            {import.meta.env.MODE}
          </span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Version</span>
          <span className="cmd-meta-value">v{health.version}</span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">AI Provider</span>
          <span className="cmd-meta-value">
            {provider ? `${provider.name}` : "—"}
            {provider && (
              <span className={`health-dot ${tone(provider.health)}`} style={{ marginLeft: 6 }} />
            )}
          </span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">Time</span>
          <span className="cmd-meta-value" data-testid="cmd-clock">
            {now.toLocaleTimeString()}
          </span>
        </div>
        <div className="cmd-meta-item">
          <span className="cmd-meta-label">System Status</span>
          <span className="cmd-meta-value" style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span className={`health-dot ${tone(systemStatus)}`} />
            <span style={{ textTransform: "capitalize" }}>{systemStatus}</span>
          </span>
        </div>
      </div>

      <div className="cmd-layout">
        <div className="cmd-main">
          {/* First row — Executive KPIs */}
          <SectionCard title="Executive KPIs">
            <div className="grid stats">
              <StatCard label="Total Projects" value={work.total_projects} />
              <StatCard label="Running Tasks" value={exec.in_progress} />
              <StatCard label="AI Employees Active" value={ai.by_status.active ?? ai.total_employees} accent="ok" />
              <StatCard
                label="Pipelines Passed"
                value={`${devops.passed}/${devops.total_pipelines}`}
              />
              <StatCard label="Deployments" value={devops.deployments} />
              <StatCard label="Avg Review Score" value={quality.avg_review_score} accent="ok" />
            </div>
          </SectionCard>

          {/* Second row — Executive Health */}
          <SectionCard title="Executive Health">
            <div className="cmd-health-row">
              <HealthPill label="Company" status={companyStatus} />
              <HealthPill label="AI" status={ai.organization_health} />
              <HealthPill label="Repository" status={repoStatus} />
              <HealthPill label="Knowledge" status={knowledge.knowledge_health} />
              <HealthPill label="Provider" status={provider?.health ?? "unknown"} />
              <HealthPill label="Deployment" status={systemStatus} />
            </div>
          </SectionCard>

          {/* Third row — Project Overview */}
          <SectionCard
            title="Project Overview"
            action={
              <Link to="/projects" className="btn btn-sm">
                Projects
              </Link>
            }
          >
            <div className="grid stats">
              <StatCard label="Active Projects" value={work.total_projects} />
              <StatCard
                label="Blocked Tasks"
                value={work.blocked_tasks}
                accent={work.blocked_tasks > 0 ? "warn" : "ok"}
              />
              <StatCard label="Velocity" value={work.velocity} hint="completed sprints" />
              <StatCard label="Total Tasks" value={work.total_tasks} />
            </div>
            <div className="cmd-split">
              <div>
                <div className="cmd-subhead">Sprint Progress</div>
                {work.sprint_progress.length === 0 ? (
                  <p className="muted">No active sprints.</p>
                ) : (
                  <div className="mini-list">
                    {work.sprint_progress.map((s) => (
                      <div key={s.sprint_number} className="mini-item">
                        <span>Sprint {s.sprint_number}</span>
                        <span className="muted">
                          {s.done}/{s.total} · v{s.velocity}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              <div>
                <div className="cmd-subhead">Upcoming Deadlines</div>
                {work.upcoming_deadlines.length === 0 ? (
                  <p className="muted">No upcoming deadlines.</p>
                ) : (
                  <div className="mini-list">
                    {work.upcoming_deadlines.map((d, i) => (
                      <div key={i} className="mini-item">
                        <span>{d.name}</span>
                        <span className="muted">{d.due_date}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </SectionCard>

          {/* Fourth row — AI Company */}
          <SectionCard
            title="AI Company"
            action={
              <Link to="/ai" className="btn btn-sm">
                AI Company
              </Link>
            }
          >
            <div className="grid stats">
              <StatCard
                label="CEO Status"
                value={ai.ceo_present ? "Present" : "Absent"}
                accent={ai.ceo_present ? "ok" : "warn"}
              />
              <StatCard label="Current Executions" value={orch.running_executions} />
              <StatCard label="Queue Size" value={exec.ai_work_queue} />
              <StatCard
                label="Review Queue"
                value={exec.pending_reviews}
                accent={exec.pending_reviews > 0 ? "warn" : "ok"}
              />
            </div>
          </SectionCard>

          {/* Fifth row — Development */}
          <SectionCard
            title="Development"
            action={
              <Link to="/development" className="btn btn-sm">
                Development
              </Link>
            }
          >
            <div className="grid stats">
              <StatCard label="Open PRs" value={development.open_pull_requests} />
              <StatCard
                label="Quality Gates Eligible"
                value={quality.approval_eligible}
                accent="ok"
              />
              <StatCard label="Code Reviews" value={quality.total_gate_runs} />
              <StatCard
                label="Pending Approvals"
                value={development.pending_approvals}
                accent={development.pending_approvals > 0 ? "warn" : "ok"}
              />
            </div>
          </SectionCard>

          {/* Sixth row — Infrastructure */}
          <SectionCard
            title="Infrastructure"
            action={
              <Link to="/devops" className="btn btn-sm">
                DevOps
              </Link>
            }
          >
            <div className="grid stats">
              <StatCard label="Pipelines" value={devops.total_pipelines} />
              <StatCard label="Deployments" value={devops.deployments} />
              <StatCard
                label="Open Incidents"
                value={devops.open_incidents}
                accent={devops.open_incidents > 0 ? "warn" : "ok"}
              />
              <StatCard
                label="Monitoring"
                value={
                  sys ? (
                    <span style={{ textTransform: "capitalize" }}>{sys.overall_status}</span>
                  ) : (
                    "—"
                  )
                }
                accent={tone(sys?.overall_status)}
                hint={sys ? `cpu ${sys.cpu_pct}% · mem ${sys.memory_pct}% · disk ${sys.disk_pct}%` : ""}
              />
            </div>
          </SectionCard>

          {/* Department overview (existing) */}
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

          {/* Employee workspace (existing) */}
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

        {/* Right side panel */}
        <aside className="cmd-aside">
          <SectionCard title="Company Health">
            <CompanyHealth health={health} />
          </SectionCard>

          <SectionCard title="Recent Activity">
            <ActivityFeed items={activity} />
          </SectionCard>

          <SectionCard title="Latest AI Tasks">
            {development.recent_tasks.length === 0 ? (
              <p className="muted">No development tasks yet.</p>
            ) : (
              <div className="mini-list">
                {development.recent_tasks.slice(0, 6).map((t) => (
                  <div key={t.id} className="mini-item">
                    <span className="mini-item-title">
                      {t.code} · {t.title}
                    </span>
                    <span className="badge prio-low">{t.status}</span>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Latest Pipelines">
            {devops.recent_pipelines.length === 0 ? (
              <p className="muted">No pipelines yet.</p>
            ) : (
              <div className="mini-list">
                {devops.recent_pipelines.slice(0, 6).map((p) => (
                  <div key={p.id} className="mini-item">
                    <span className="mini-item-title">
                      {p.code} · {p.environment_target}
                    </span>
                    <span className="badge prio-low">{p.status}</span>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Latest Quality Gates">
            {quality.recent.length === 0 ? (
              <p className="muted">No gate runs yet.</p>
            ) : (
              <div className="mini-list">
                {quality.recent.slice(0, 6).map((r, i) => (
                  <div key={i} className="mini-item">
                    <span className="mini-item-title">Score {r.overall_score}</span>
                    <span className={`badge ${r.approval_eligible ? "prio-low" : "prio-medium"}`}>
                      {r.approval_eligible ? "eligible" : "blocked"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Latest Knowledge">
            {knowledge.recent_knowledge.length === 0 ? (
              <p className="muted">No documents yet.</p>
            ) : (
              <div className="mini-list">
                {knowledge.recent_knowledge.slice(0, 6).map((d) => (
                  <div key={d.id} className="mini-item">
                    <span className="mini-item-title">{d.title}</span>
                    <span className="badge prio-low">{d.status}</span>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Organization Snapshot">
            <OrgSnapshot employees={employees} />
          </SectionCard>
        </aside>
      </div>
    </div>
  );
}
