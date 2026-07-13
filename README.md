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
├─ backend/             WES OS — Company Engine backend (FastAPI + SQLAlchemy)
├─ frontend/            WES OS — Company Engine frontend (React + Vite + TypeScript)
├─ docs/                Company + implementation documentation
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

## WES OS — Company Engine

WES OS is the WES Operating System. Its first production module, the **Core
Company Engine** (Sprint 02), manages the foundational organizational entities —
**Company, Departments, Employees** — that every future module depends on.

- Backend: [`/backend`](./backend/README.md) — FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Frontend: [`/frontend`](./frontend/README.md) — React, Vite, TypeScript
- Docs: [`docs/implementation/`](./docs/implementation/README.md) — architecture, API reference, setup

Quick start: `docker compose up --build` (see the [Setup Guide](./docs/implementation/setup.md)).

## Blueprint

The Blueprint is the source of truth for how WES operates, organized into ten volumes covering foundation, organization, roles, engineering, AI systems, technology, project management, security & quality, knowledge management, and automation. See [Blueprint/README.md](./Blueprint/README.md).

## Company

The operational company structure is documented under [Company/](./Company/README.md), with departments in [Departments/](./Departments/README.md) and roles in [Employees/](./Employees/README.md).

## License

Released under the [MIT License](./LICENSE).
