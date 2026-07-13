# WES Backend

FastAPI (Python) backend for the WES Web Application. Architecture is frozen in [../docs/01-Architecture.md](../docs/01-Architecture.md); API strategy in [../docs/05-API-Strategy.md](../docs/05-API-Strategy.md).

## Requirements

- Python 3.11+
- PostgreSQL 15+

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn app.main:app --reload
```

The API runs at `http://localhost:8000`. Health check: `GET /health`. Versioned routes live under `/api/v1`.

## Structure (`app/`)

| Folder | Layer |
|--------|-------|
| `main.py` | Application entrypoint. |
| `core/` | Config and security. |
| `api/v1/` | Versioned routers (HTTP layer). |
| `services/` | Business logic. |
| `repositories/` | Data access. |
| `models/` | SQLAlchemy ORM entities. |
| `schemas/` | Pydantic request/response schemas. |
| `db/` | Session and migration base. |

> Sprint 01 provides the layered skeleton and a health endpoint only. Modules are implemented in later sprints per the [roadmap](../docs/06-Development-Roadmap.md).
