# WES Web Application

The **operating system of WORLD Engineering Studio (WES)** — the application through which WES runs the company and manages its projects, starting with [Project-001: WORLD](../Projects/Project-001-WORLD/README.md).

**Sprint:** 01 (Architecture Foundation) · **Status:** Architecture Frozen · no features implemented yet.

## Overview

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js (React + TypeScript) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Auth | OAuth2 + JWT |
| API | REST, versioned `/api/v1` |

Full rationale is in the [engineering docs](./docs/README.md).

## Structure

```
wes-app/
├─ docs/       Architecture, tech decisions, module map, DB plan, API strategy, roadmap
├─ frontend/   Next.js application
├─ backend/    FastAPI application
└─ infra/      docker-compose and local environment
```

## Local Development

Run the full stack with Docker:

```bash
cd wes-app/infra
docker compose up --build
```

Or run each app individually — see [frontend/README.md](./frontend/README.md) and [backend/README.md](./backend/README.md).

## Documentation

Start with the [engineering docs index](./docs/README.md). The application follows the [WES Blueprint](../Blueprint/README.md) as the single source of truth.
