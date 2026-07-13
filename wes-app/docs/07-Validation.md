# Sprint 02 — Validation Report

**Scope:** Validate, stabilize, and harden the Company Engine (Company, Department, Employee). No new features.

## Summary

The implementation was audited, hardened, and wired into an automated validation pipeline. Because the authoring environment has **no package-registry network access and no Docker**, the stack could not be executed there. Validation is therefore split into three honest tiers:

- **Verified here:** syntax compilation of all backend modules; dependency-free logic (exceptions, error envelope, pagination math); a static audit that found and fixed a real build bug.
- **Automated (runs in CI on GitHub):** ruff lint, PostgreSQL migration, DB persistence check, pytest, frontend lint, Vitest, and `next build`.
- **Manual (one command):** `docker compose up` for a full local run.

## 1. Local Development

Run the full stack:

```bash
cd wes-app/infra
docker compose up --build          # starts postgres + backend (:8000) + frontend (:3000)
docker compose exec backend alembic upgrade head   # create schema (first run)
docker compose exec backend python -m app.seed     # optional: seed company/depts/employees
```

Environment variables load from `.env` files (see `.env.example` in `backend/` and `frontend/`) and from `docker-compose.yml`.

## 2. Database

- Alembic migration `0001_initial` creates `companies`, `departments`, `employees` with indexes and the employee→department FK (`ON DELETE SET NULL`).
- CI runs `alembic upgrade head` against a real PostgreSQL 16 service, then `scripts/validate_db.py` performs a create/read/delete against it.
- Seed data: `python -m app.seed` (idempotent) loads 1 company, 6 departments, 13 employees.

## 3. API

Endpoints under `/api/v1` (standards frozen in Sprint 01):

| Resource | Endpoints |
|----------|-----------|
| Companies | `GET/POST /companies`, `GET/PATCH/DELETE /companies/{id}` |
| Departments | `GET/POST /departments`, `GET/PATCH/DELETE /departments/{id}` |
| Employees | `GET/POST /employees` (+ `?departmentId=`), `GET/PATCH/DELETE /employees/{id}` |
| System | `GET /system/metadata` |

Validated by pytest: request validation (422), conflicts (409), not-found (404), persistence, pagination envelope, and the department relationship. Interactive docs at `/docs`.

## 4. Frontend

- App shell with sidebar navigation (Dashboard, Departments, Employees).
- Company dashboard (profile + live counts), Departments listing, Employees listing — all consuming the API via a typed client with error handling.
- `next build` is exercised in CI. A build bug (unqualified `React.ReactNode` in module files) was found in audit and fixed.

## 5. Testing

| Suite | Tool | Runs in |
|-------|------|---------|
| Backend API/unit | pytest (SQLite in-memory) | CI |
| DB persistence | scripts/validate_db.py (PostgreSQL) | CI |
| Frontend component | Vitest + Testing Library | CI |

## 6. Code Quality

- Backend: `ruff check .` in CI.
- Frontend: `npm run lint` (ESLint / next core-web-vitals) in CI.

## 7. Docker

| Command | Purpose |
|---------|---------|
| `docker compose up --build` | Build and start the full stack. |
| `docker compose down` | Stop and remove containers. |
| `docker compose down -v` | Stop and remove the persistent DB volume. |
| `docker compose up --build --force-recreate` | Clean rebuild. |

The database persists in the named volume `wes_db_data` across `up`/`down` (removed only with `-v`).

## 8. CI/CD

The pipeline is defined in [`../ci/github-actions-ci.yml`](../ci/github-actions-ci.yml). It runs on every push and pull request to `main` and **fails if any lint, migration, test, or build step fails**. See [`../ci/README.md`](../ci/README.md) to enable it (one step — the automation token could not write to `.github/workflows/`).

## 9. Known Issues / Limitations

- **Not executed in the authoring environment** — no network/Docker here; runtime validation is delegated to CI and the local `docker compose` run.
- **CI not yet enabled in `.github/workflows/`** — requires the one-time step in `wes-app/ci/README.md`.
- **Dependency versions are pinned but unproven against a live install** — the first CI run confirms resolution; commit lockfiles afterward.
- **No authentication yet** — endpoints are open; JWT auth is the next sprint (per the API strategy).

---

_See also: [Architecture](./01-Architecture.md) · [API Strategy](./05-API-Strategy.md) · [Roadmap](./06-Development-Roadmap.md)_
