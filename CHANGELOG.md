# Changelog

All notable changes to WES OS are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this
project adheres to [Semantic Versioning](https://semver.org/).

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
