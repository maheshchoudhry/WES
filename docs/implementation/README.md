# WES OS — Implementation Documentation

Implementation documentation for **WES OS**, the WES Operating System. This is
distinct from the [Blueprint](../../Blueprint/README.md) (the frozen operating
framework) — it documents the software as built.

## Modules

| Sprint | Module | Status |
|--------|--------|--------|
| Sprint 02 | [Core Company Engine](./company-engine.md) — Company, Departments, Employees | Implemented |
| Sprint 03 | [Founder Workspace & Executive Dashboard](./dashboard.md) | Implemented |

## Contents

- [Company Engine](./company-engine.md) — architecture, domain model, business rules
- [Founder Dashboard](./dashboard.md) — dashboard aggregation, widgets, screenshots
- [API Reference](./api.md) — every REST endpoint, request/response shapes, error codes
- [Setup Guide](./setup.md) — run locally and with Docker

## Codebase

| Path | Description |
|------|-------------|
| [`/backend`](../../backend/README.md) | FastAPI + SQLAlchemy + Alembic service |
| [`/frontend`](../../frontend/README.md) | React + Vite + TypeScript UI |
| [`/docker-compose.yml`](../../docker-compose.yml) | Postgres + backend + frontend orchestration |
