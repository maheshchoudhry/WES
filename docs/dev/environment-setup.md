# Environment Setup

## Required toolchain

| Tool | Minimum | Check |
|------|---------|-------|
| Python | 3.11 | `python3 --version` |
| Node.js | 18 | `node -v` |
| npm | any | `npm -v` |
| Git | any | `git --version` |
| Docker | optional | `docker --version` |

`bootstrap.sh` and `dev.sh` validate all of the above automatically and print a
per-tool ✓ / ✗, plus virtualenv presence and whether ports 8000 / 5173 are free.

## Environment variables

`.env` files are created automatically from the `.env.example` templates. Key
backend variables (`WES_` prefix):

| Variable | Default | Purpose |
|----------|---------|---------|
| `WES_DATABASE_URL` | SQLite `wes_os.db` | Database URL (PostgreSQL in production) |
| `WES_JWT_SECRET` | dev secret | **Set a strong value in production** |
| `WES_ACCESS_TOKEN_MINUTES` | 30 | Access token lifetime |
| `WES_REFRESH_TOKEN_DAYS` | 7 | Refresh token lifetime |
| `WES_AUTO_MIGRATE` | true (app) / false (scripts) | Migrate on startup |
| `WES_SEED_ON_START` | true (app) / false (scripts) | Seed on startup |
| `WES_CORS_ORIGINS` | localhost + 127.0.0.1 dev origins | Allowed frontend origins |

Frontend (`VITE_` prefix): leave `VITE_API_BASE_URL` empty to use the dev proxy;
`VITE_API_PROXY` defaults to `http://127.0.0.1:8000`.

## Ports

- Backend: `8000`
- Frontend: `5173`

If a port is in use, `dev.sh` / `reset.sh` stop existing WES processes first.
To free a port manually: `lsof -nP -iTCP:8000 -sTCP:LISTEN` then `kill <pid>`.

## Manual virtualenv (if not using the scripts)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```
