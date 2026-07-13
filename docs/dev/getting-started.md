# Getting Started

Get WES OS running from a fresh clone in two commands.

## Prerequisites

- **Python** 3.11+
- **Node** 18+ and **npm**
- **Git**
- Docker is optional (only for the containerized deployment path).

## 1. Bootstrap (once per clone)

```bash
git clone <repo-url> WES
cd WES
./scripts/bootstrap.sh
```

`bootstrap.sh` installs backend and frontend dependencies, creates `.env` files,
prepares and seeds the database, and verifies the installation.

## 2. Start

```bash
./scripts/dev.sh
```

Open:

- Frontend — http://localhost:5173
- Backend API — http://127.0.0.1:8000
- Swagger / OpenAPI — http://127.0.0.1:8000/docs

## 3. Sign in

Seeded development accounts (password `WesOs2026!`):

| Email | Role |
|-------|------|
| `wes-emp-001@wes.studio` | Founder |
| `wes-emp-002@wes.studio` | Director |
| `wes-emp-004@wes.studio` | Department Head |
| `wes-emp-006@wes.studio` | Employee |
| `wes-emp-013@wes.studio` | Read Only |

## Everyday commands

| Command | What it does |
|---------|--------------|
| `./scripts/dev.sh` | Start the full stack (one command) |
| `./scripts/stop.sh` | Stop backend + frontend |
| `./scripts/reset.sh` | Wipe DB, re-migrate, re-seed, restart |
| `./scripts/health.sh` | Verify a running system |
| `./scripts/test.sh` | Run backend + frontend tests |
| `./scripts/lint.sh` | Lint (ruff, black, tsc, prettier) |
| `./scripts/format.sh` | Auto-format everything |
| `./scripts/migrate.sh` | Apply migrations |
| `./scripts/seed.sh` | Seed the database |

See [Developer Guide](./developer-guide.md) and [Troubleshooting](./troubleshooting.md).
