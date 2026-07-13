import { Link } from "react-router-dom";

import { aiApi, type AISummary } from "../api/ai";
import { dashboardApi } from "../api/dashboard";
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
}

async function loadDashboard(): Promise<DashboardData> {
  const [stats, departments, employees, activity, health, ai] = await Promise.all([
    dashboardApi.stats(),
    dashboardApi.departments(),
    dashboardApi.employees(),
    dashboardApi.activity(8),
    dashboardApi.health(),
    aiApi.summary(),
  ]);
  return {
    stats: stats.data,
    departments: departments.data,
    employees: employees.data,
    activity: activity.data,
    health: health.data,
    ai: ai.data,
  };
}

export function Dashboard() {
  const { data, loading, error } = useAsync(loadDashboard, []);

  if (loading) return <Loading label="Loading dashboard…" />;
  if (error) return <ErrorNotice message={error} />;
  if (!data) return null;

  const { stats, departments, employees, activity, health, ai } = data;
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
