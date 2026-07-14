# Changelog

All notable changes to WES OS are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/).

## [0.2.0-alpha] — 2026-07-14

The **AI Company Work Management Platform**. Builds on v0.1.0-alpha with a
first-class AI organization and an operational work-execution engine — the AI
company can now receive, own, track, and complete software work. Runtime verified.

### Sprint 06 Summary — AI Company Core

AI employees as first-class entities: AI departments, roles, capabilities,
employees (with reporting hierarchy), responsibilities, and KPIs. Workspaces:
AI Company dashboard, employee directory, employee profile, organization chart,
and department view. Soft-delete only; RBAC-guarded.

### Sprint 07 Summary — AI Work Management & Project Execution Engine

Projects, milestones, sprints, work items (tasks), assignments, dependencies,
statuses, priorities, and an activity timeline. Kanban Task Board, project and
task detail views, an assignment engine that routes work to AI employees, and
Founder/AI dashboard work analytics.

### Architecture Changes

No architectural change — both sprints reuse the frozen layered design
(API → Service → Repository → ORM), the standard response envelope, and Sprint 04
RBAC. The Blueprint is unchanged.

### Database Changes

- Migration `0003_ai_company_core`: `ai_departments`, `ai_roles`,
  `ai_capabilities`, `ai_employees`, `ai_responsibilities`, `ai_kpis`,
  `ai_employee_capabilities`.
- Migration `0004_work_management`: `projects`, `milestones`, `project_sprints`,
  `work_items`, `assignments`, `work_dependencies`, `activity_log`, `comments`,
  `attachments_metadata`.

### Backend

New modules: AI organization (organization + reporting services) and work
management (project/sprint/task/assignment/activity + analytics). New permissions
`ai:read/update/manage` and `work:read/write`. Endpoints under `/ai-employees`,
`/ai-roles`, `/ai-departments`, `/ai-org/*`, `/projects`, `/sprints`,
`/milestones`, `/tasks`, `/assignments`, `/activity`, `/work/*`.

### Frontend

AI Company workspaces (dashboard, directory, profile, org chart, department view)
and Work Management screens (Projects, Project Detail, Kanban Task Board, Task
Detail). New "AI Company" and "Work" navigation sections; Founder and AI
dashboards extended with organization and work summaries.

### Testing

Backend **132** tests (pytest); frontend **25** tests (vitest). ruff/black/prettier
clean; one-command health suite passing (10/10).

### Known Issues

- Kanban uses a status selector (drag-and-drop-ready), not native HTML5 DnD.
- Attachments are metadata-only (no upload); comments/dependencies have minimal UI.
- Analytics load full tables in memory (fine at current scale).
- Bearer-token auth; dev secret and seeded passwords are placeholders.
- Docker/PostgreSQL path is config-validated only in local dev.

### Roadmap

Sprint 08: true drag-and-drop Kanban, sprint planning & burndown, notifications,
department-scoped work RBAC and a "My Work" view, and file attachments.

## [0.1.0-alpha] — 2026-07-13

First operational release of WES OS — the WORLD Engineering Studio Operating
System. Delivers the foundation: a Company Engine, an Executive Dashboard,
Authentication & RBAC, and a one-command developer platform. Runtime verified.

### Sprint Summary

| Sprint | Title | Outcome |
|--------|-------|---------|
| 01 | Architecture Foundation | Frozen stack & standards (Blueprint) |
| 02 | Company Engine | Company / Department / Employee domains + CRUD APIs |
| 03 | Founder Workspace & Executive Dashboard | Live executive dashboard + reusable widgets |
| 04 | Authentication & RBAC | JWT auth, refresh tokens, five roles, permission middleware |
| 05 | Developer Experience & Development Platform | One-command dev environment |

### Major Features

- **Company Engine** — Company, Department, and Employee modules with validation,
  business rules, and REST CRUD APIs (standard `{data}` / `{error}` envelope).
- **Executive Dashboard** — company overview, department cards, employee workspace,
  organization snapshot, company health, and recent activity on live data.
- **Authentication & RBAC** — email/password login (bcrypt), JWT access + refresh
  tokens, logout invalidation, and five roles (Founder, Director, Department Head,
  Employee, Read Only) enforced by reusable permission middleware.
- **Developer Platform** — `./scripts/dev.sh` starts, migrates, seeds, and
  health-verifies the whole stack in one command; plus `stop`, `reset`, `bootstrap`,
  `migrate`, `seed`, `health`, `test`, `lint`, `format`.
- **Self-initializing backend** — applies migrations and seeds on startup.

### Architecture

- **Backend** — Python, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2; layered
  API → Service → Repository → ORM. PostgreSQL in production; SQLite for local/tests.
- **Frontend** — TypeScript, React 18, Vite, React Router.
- **Auth** — JWT (HS256); RBAC permission matrix.
- **Database** — migrations `0001_initial`, `0002_auth_fields`; seeded WES org
  (1 company, 6 departments, 13 employees, one of each role).
- **Tests** — 77 backend (pytest), 20 frontend (vitest).

### Known Limitations

- Bearer-token auth (not httpOnly cookies); dev secret and seeded passwords must
  be changed before deployment.
- Director/Department-Head writes are company-wide, not yet department-scoped.
- Activity feed is derived from timestamps (no dedicated audit log).
- Container (PostgreSQL/Docker) path is configured but not exercised in local dev.
- Alpha quality: foundation only — no Projects, Tasks, Reports, or Knowledge Base yet.

### Next Roadmap

- CI pipeline (lint + test), pre-commit hooks.
- Password management (change/reset) and department-scoped permissions.
- Audit log; Projects module (the dashboard reserves its slot).
- Dockerized dev parity.

[0.1.0-alpha]: https://example.com/WES/releases/tag/v0.1.0-alpha
