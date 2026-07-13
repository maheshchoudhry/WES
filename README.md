# WES

**WORLD Engineering Studio**

WES is an independent AI Engineering Company. Its purpose is to design, manage, review, and build software projects.

---

## Mission

WES exists to engineer software with clarity, discipline, and long-term vision. The studio combines AI systems with structured engineering practice to deliver reliable, well-documented, and maintainable projects.

## Current Stage

The [Blueprint](./Blueprint) (v1.0) is complete and is the official operating reference. WES is now activated as an operational company structure, with departments, employees, and its first project initialized.

## Projects

| ID | Project | Status |
|-------------|---------|-------------|
| Project-001 | WORLD   | Not Started |

WORLD is the first official project of WES. It is maintained as a fully independent repository and is not part of this repository.

## Repository Structure

```
WES/
├─ README.md            Project overview
├─ LICENSE              MIT License
├─ .gitignore           Ignored files
├─ docker-compose.yml   WES OS local orchestration (Postgres + backend + frontend)
├─ scripts/             Developer platform (dev, stop, reset, test, health, …)
├─ backend/             WES OS — backend (FastAPI + SQLAlchemy + Alembic)
├─ frontend/            WES OS — frontend (React + Vite + TypeScript)
├─ logs/                Runtime logs, pids, health reports (git-ignored)
├─ docs/                Company, implementation, and developer documentation
├─ Blueprint/           Operating framework (Vol. 01–10) — official reference
├─ Company/             Company profile, org chart, directories, policies
├─ Departments/         One directory per department
├─ Employees/           One directory per core AI employee
├─ Projects/            Project management (Project-001: WORLD)
├─ Standards/           Engineering standards (placeholders)
├─ Templates/           Reusable templates (placeholders)
├─ KnowledgeBase/       Knowledge management structure
├─ Meeting-Notes/       Meeting records
├─ Reports/             Status and review reports
└─ Assets/              Shared assets
```

## WES OS — Quick Start

WES OS is the WES Operating System. It runs from **one command** — no manual
backend, frontend, migration, or seed steps.

```bash
git clone <repo-url> WES
cd WES
./scripts/bootstrap.sh     # install deps, create .env, prepare DB (once)
./scripts/dev.sh           # start everything + verify
```

Then open:

- **Frontend** — http://localhost:5173
- **Backend API** — http://127.0.0.1:8000
- **Swagger** — http://127.0.0.1:8000/docs

Sign in with a seeded account (password `WesOs2026!`), e.g. `wes-emp-001@wes.studio` (Founder).

| Command | Purpose |
|---------|---------|
| `./scripts/dev.sh` | Start the full stack (one command) |
| `./scripts/stop.sh` | Stop backend + frontend |
| `./scripts/reset.sh` | Wipe DB, migrate, seed, restart |
| `./scripts/health.sh` | Verify a running system |
| `./scripts/test.sh` · `lint.sh` · `format.sh` | Tests / lint / format |

Full guides: [Getting Started](./docs/dev/getting-started.md) ·
[One-Command Startup](./docs/dev/one-command-startup.md) ·
[Developer Guide](./docs/dev/developer-guide.md) ·
[Environment Setup](./docs/dev/environment-setup.md) ·
[Troubleshooting](./docs/dev/troubleshooting.md) ·
[Common Errors](./docs/dev/common-errors.md)

### Modules

The WES OS application (`backend/` + `frontend/`) delivers, per sprint:

- **Company Engine** — Company, Departments, Employees ([docs](./docs/implementation/company-engine.md))
- **Founder Dashboard** — executive overview on live data ([docs](./docs/implementation/dashboard.md))
- **Authentication & RBAC** — JWT auth, five roles ([docs](./docs/implementation/auth.md))

- Backend: [`/backend`](./backend/README.md) — FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Frontend: [`/frontend`](./frontend/README.md) — React, Vite, TypeScript
- Docs: [`docs/implementation/`](./docs/implementation/README.md) and [`docs/dev/`](./docs/dev/getting-started.md)

Container path (optional): `docker compose up --build` (see the [Setup Guide](./docs/implementation/setup.md)).

## Blueprint

The Blueprint is the source of truth for how WES operates, organized into ten volumes covering foundation, organization, roles, engineering, AI systems, technology, project management, security & quality, knowledge management, and automation. See [Blueprint/README.md](./Blueprint/README.md).

## Company

The operational company structure is documented under [Company/](./Company/README.md), with departments in [Departments/](./Departments/README.md) and roles in [Employees/](./Employees/README.md).

## License

Released under the [MIT License](./LICENSE).
