# Common Errors

A quick lookup table. For detailed guidance see [Troubleshooting](./troubleshooting.md).

| Error / symptom | Cause | Fix |
|-----------------|-------|-----|
| `no such table: companies` | DB not migrated | `./scripts/migrate.sh` (or `dev.sh`) |
| "Something went wrong" (dashboard) | Frontend can't reach API as JSON | `./scripts/dev.sh` (uses proxy); or set `VITE_API_BASE_URL` |
| `401 Unauthorized` on all APIs | Not signed in / token expired | Sign in again; token auto-refreshes |
| `403 Forbidden` after login | Role lacks permission (RBAC) | Use a higher-privilege account (Founder) |
| `port 8000/5173 already in use` | Stale process | `./scripts/stop.sh` |
| `backend import failed` (bootstrap) | Deps missing | `./scripts/bootstrap.sh` |
| `Frontend failed to start` | `node_modules` missing | `cd frontend && npm install` |
| Login returns `401` for seeded user | DB not seeded | `./scripts/seed.sh` |
| `Refresh token has been revoked` | Logged out elsewhere | Sign in again |
| Health check `Frontend running` fails | Vite not up | Check `logs/frontend.log` |

Every script returns exit code `0` on success and non-zero on failure, so they
compose in CI and other automation.
