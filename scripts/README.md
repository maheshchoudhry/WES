# WES OS — Developer Scripts

One-command developer platform. All scripts are macOS-compatible (bash 3.2),
idempotent, and return proper exit codes. They share `lib/common.sh`.

| Script | Purpose |
|--------|---------|
| `bootstrap.sh` | Fresh-clone setup: install deps, create `.env`, prepare DB, verify |
| `dev.sh` | One-command startup + full health verification |
| `stop.sh` | Stop backend + frontend |
| `reset.sh` | Wipe DB → migrate → seed → restart |
| `migrate.sh` | Apply database migrations |
| `seed.sh` | Seed the WES organization (idempotent) |
| `health.sh` | Verify backend/frontend/DB/JWT/auth + all APIs |
| `test.sh` | Backend `pytest` + frontend `vitest` |
| `lint.sh` | ruff + black --check + tsc + prettier --check |
| `format.sh` | ruff --fix + black + prettier --write |

See [docs/dev/](../docs/dev/getting-started.md) for full guides.
