# Developer Guide

How WES OS is built and how to work on it.

## Repository layout

```
WES/
├─ scripts/            Developer platform (one-command dev, test, lint, health, …)
│  └─ lib/common.sh    Shared script library (paths, checks, start/stop, health)
├─ backend/            FastAPI + SQLAlchemy + Alembic (Company Engine, Dashboard, Auth)
├─ frontend/           React + Vite + TypeScript
├─ logs/               Runtime logs, pids, health reports (git-ignored)
├─ docs/
│  ├─ implementation/  What was built each sprint (Company Engine, Dashboard, Auth)
│  └─ dev/             This developer documentation
└─ Blueprint/ …        Frozen operating framework (do not modify)
```

## The developer scripts

Every script sources `scripts/lib/common.sh`, is idempotent, and returns a proper
exit code (`0` on success).

| Script | Purpose |
|--------|---------|
| `bootstrap.sh` | Fresh-clone setup: install deps, create `.env`, prepare DB, verify |
| `dev.sh` | One-command startup with full health verification |
| `stop.sh` | Stop backend + frontend |
| `reset.sh` | Wipe DB → migrate → seed → restart |
| `migrate.sh` | `alembic upgrade head` |
| `seed.sh` | Seed the WES organization (idempotent) |
| `health.sh` | Verify backend/frontend/DB/JWT/auth + all APIs |
| `test.sh` | Backend `pytest` + frontend `vitest` |
| `lint.sh` | ruff + black --check + tsc + prettier --check |
| `format.sh` | ruff --fix + black + prettier --write |

### Configuration (scripts/lib/common.sh)

- Backend `127.0.0.1:8000`, frontend `localhost:5173`.
- Dev database: SQLite at `backend/wes_os.db` (absolute path, cwd-independent).
- Scripts export `WES_DATABASE_URL`, `WES_AUTO_MIGRATE=false`, `WES_SEED_ON_START=false`
  so migration/seeding is explicit and deterministic.
- Logs and pids under `logs/`.

## Backend development

```bash
cd backend
source ../.venv/bin/activate
uvicorn app.main:app --reload      # or use ./scripts/dev.sh
pytest                             # tests
alembic revision --autogenerate -m "message"   # new migration
```

Architecture: API → Service → Repository → ORM, with Pydantic schemas at the
boundary and a standard `{data}` / `{error}` response envelope. Auth is JWT +
RBAC (see [implementation/auth.md](../implementation/auth.md)).

## Frontend development

```bash
cd frontend
npm run dev          # dev server (proxies /api to the backend)
npm run test         # vitest
npm run typecheck    # tsc --noEmit
npm run build        # production build
```

## Logs

- `logs/backend.log` — backend server output
- `logs/frontend.log` — frontend dev server output
- `logs/startup.log` — migration/seed output during startup
- `logs/health-report.txt` — latest health check result
- `logs/backend.pid`, `logs/frontend.pid` — process ids used by `stop.sh`

## Coding standards

Follow Blueprint Vol. 04 (Engineering System): small focused changes, Conventional
Commits (`type(scope): summary`), reviewed via PR, tests + docs updated. Run
`./scripts/format.sh` then `./scripts/lint.sh` before committing.
