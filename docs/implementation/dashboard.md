# Founder Workspace & Executive Dashboard (Sprint 03)

The Founder Workspace is the first operational interface of WES OS. It gives the
Founder an at-a-glance view of the company, built entirely on **live Company
Engine data** (Sprint 02). It adds **no new database tables** — it is a read/
aggregation layer over existing data.

## Backend — dashboard aggregation

`app/services/dashboard.py` composes read models by reusing the existing
repositories (`CompanyRepository`, `DepartmentRepository`, `EmployeeRepository`).
No business logic is duplicated and no data is mutated.

Endpoints (all `GET`, read-only, under `/api/v1/dashboard`):

| Path | Returns |
|------|---------|
| `/dashboard/company-summary` | Company + department/employee counts |
| `/dashboard/stats` | Totals and breakdowns (by status, by authority) |
| `/dashboard/departments` | Per-department employee counts and status |
| `/dashboard/employees` | Employee directory with resolved department & manager names |
| `/dashboard/activity` | Recent activity derived from entity create/update timestamps |
| `/dashboard/health` | API + database health and entity counts |

The activity feed is derived from `created_at`/`updated_at` (created when equal,
updated otherwise) — no separate audit table is introduced in this sprint.

## Frontend — Executive Dashboard

Route `/` renders the **Founder Dashboard**. The Company Engine CRUD pages move to
`/company`, `/departments`, `/employees` (editing stays in the Company Engine;
the dashboard is read-only).

### Reusable widgets (`src/components/widgets/`)

Designed to be reused across future modules:

- `StatCard` — statistic tile
- `SectionCard` — titled panel
- `ActivityFeed` — recent activity list
- `CompanyHealth` — system/company health
- `QuickActions` — quick navigation
- `OrgSnapshot` — reporting-hierarchy tree
- `DepartmentCard` — department summary card

### Dashboard sections

Company overview stats · Department Overview (cards) · Employee Workspace
(read-only directory with manager/department) · Quick Actions · Company Health ·
Organization Snapshot (reporting hierarchy) · Recent Activity.

### Navigation

Active: Dashboard · Company · Departments · Employees. Reserved placeholders
(shown disabled): Projects · Tasks · Knowledge · Reports · AI Hub · Settings.

## Screenshots

Captured from the running stack (seeded WES organization):

| Screen | Image |
|--------|-------|
| Founder Dashboard | [`screenshots/01-dashboard.png`](./screenshots/01-dashboard.png) |
| Company | [`screenshots/02-company.png`](./screenshots/02-company.png) |
| Departments | [`screenshots/03-departments.png`](./screenshots/03-departments.png) |
| Employees | [`screenshots/04-employees.png`](./screenshots/04-employees.png) |
