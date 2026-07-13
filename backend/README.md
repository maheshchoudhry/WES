# WES Company Engine — Backend

Production backend for the **WES Core Company Engine** (Sprint 02). Implements the
Company, Department, and Employee domains that every future WES OS module depends on.

Stack (frozen in Sprint 01 — Blueprint Vol. 06): **Python · FastAPI · SQLAlchemy 2 ·
Alembic · Pydantic v2 · PostgreSQL** (SQLite for local/tests).

## Architecture

A layered architecture keeps concerns separated:

```
API (FastAPI routers)      app/api/v1/        HTTP, request/response envelope
  → Service layer          app/services/      business rules, validation, orchestration
    → Repository layer      app/repositories/  all database access
      → ORM models          app/models/        SQLAlchemy tables
Schemas (Pydantic)         app/schemas/       request/response contracts + field validation
Domain enums               app/domain/        shared vocabulary
Core                       app/core/          config, database, exceptions, responses
```

Services raise framework-agnostic domain exceptions (`NotFoundError`,
`ConflictError`, `ValidationError`); `app/main.py` maps them to the standard
error envelope. Each HTTP request is one transaction (unit of work in `get_db`).

## Response envelope

- Success: `{ "data": <object|array>, "meta": { "total": N } }`
- Error: `{ "error": { "code": "...", "message": "...", "details": [...] } }`

## Local development

Requires Python 3.11+.

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # defaults to SQLite; set WES_DATABASE_URL for Postgres

alembic upgrade head            # create the schema
python -m app.db.seed           # seed the WES organization (optional)
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)
```

## Tests

```bash
pytest            # 34 tests: unit + API + integration (run against in-memory SQLite)
```

## Configuration

All config comes from environment variables prefixed `WES_` (see `.env.example`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `WES_DATABASE_URL` | `sqlite:///./wes_os.db` | SQLAlchemy database URL |
| `WES_API_V1_PREFIX` | `/api/v1` | API path prefix |
| `WES_CORS_ORIGINS` | localhost:5173,3000 | Comma-separated allowed origins |
| `WES_DEBUG` | `true` | Debug flag |

## Migrations

See [`alembic/README.md`](alembic/README.md). The database URL is injected from
`WES_DATABASE_URL`; nothing is hard-coded in `alembic.ini`.
