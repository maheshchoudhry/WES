# WES Web Application

The **operating system of WORLD Engineering Studio (WES)** — the application through which WES runs the company and manages its projects, starting with [Project-001: WORLD](../Projects/Project-001-WORLD/README.md).

**Sprint:** 02 (Company Engine) · **Status:** Company / Department / Employee modules operational.

## Overview

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (React + TypeScript) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Auth | OAuth2 + JWT (upcoming) |
| API | REST, versioned `/api/v1` |

Full rationale is in the [engineering docs](./docs/README.md).

## Implemented Modules (Sprint 02)

| Module | Backend | Frontend |
|--------|---------|----------|
| Company | CRUD `/api/v1/companies` | Dashboard profile + stats |
| Departments | CRUD `/api/v1/departments` | Department listing |
| Employees | CRUD `/api/v1/employees` | Employee listing |
| System | `/api/v1/system/metadata` | Dashboard counts |

## Structure

```
wes-app/
├─ docs/       Architecture, tech decisions, module map, DB plan, API strategy, roadmap
├─ frontend/   Next.js application (app shell + Company Engine UI)
├─ backend/    FastAPI application (layered: api / services / repositories / models)
└─ infra/      docker-compose and local environment
```

## Local Development

Run the full stack with Docker:

```bash
cd wes-app/infra
docker compose up --build
```

Then apply migrations inside the backend container (first run):

```bash
docker compose exec backend alembic upgrade head
```

Or run each app individually — see [frontend/README.md](./frontend/README.md) and [backend/README.md](./backend/README.md).

## Documentation

Start with the [engineering docs index](./docs/README.md). The application follows the [WES Blueprint](../Blueprint/README.md) as the single source of truth.
