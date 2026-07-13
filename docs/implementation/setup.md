# Company Engine — Setup Guide

Two ways to run the Company Engine: **Docker Compose** (everything, including
PostgreSQL) or **manual** (run backend and frontend directly).

## Option A — Docker Compose (recommended)

Requires Docker with Compose v2.

```bash
cp .env.example .env          # local defaults are fine
docker compose up --build
```

This starts:

| Service | URL | Notes |
|---------|-----|-------|
| PostgreSQL | localhost:5432 | data persisted in the `wes_pgdata` volume |
| Backend | http://localhost:8000 | migrations run on start; docs at `/docs` |
| Frontend | http://localhost:8080 | nginx serving the built SPA, `/api` proxied to backend |

With `WES_SEED_ON_START=true` (default in `.env.example`), the backend seeds the
WES organization on first start.

## Option B — Manual

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                       # SQLite by default
uvicorn app.main:app --reload               # http://localhost:8000
```

The backend **self-initializes on startup**: it applies Alembic migrations and
seeds the WES organization automatically (controlled by `WES_AUTO_MIGRATE` and
`WES_SEED_ON_START`, both on by default). No separate migration step is needed.

To initialize the database without starting the server, or to disable
auto-initialization, use:

```bash
python -m app.db.init          # apply migrations + seed explicitly
# or run pieces manually:
alembic upgrade head
python -m app.db.seed
# to turn auto-init off:  WES_AUTO_MIGRATE=false uvicorn app.main:app
```

To use PostgreSQL instead of SQLite, set in `backend/.env`:
```
WES_DATABASE_URL=postgresql+psycopg2://wes:wes@localhost:5432/wes_os
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev                                 # http://localhost:5173
```

The dev server proxies `/api` to `http://localhost:8000`.

## Verify

```bash
# Backend health
curl http://localhost:8000/api/v1/health

# List seeded departments
curl http://localhost:8000/api/v1/departments

# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm run test
```
