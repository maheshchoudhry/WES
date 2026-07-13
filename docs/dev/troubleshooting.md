# Troubleshooting & Common Errors

Most issues are resolved by:

```bash
./scripts/stop.sh && ./scripts/reset.sh
```

## Common errors

### "Something went wrong" on the dashboard
The frontend can't reach the backend as JSON. Ensure the backend is running
(`./scripts/health.sh`) and that you started the frontend via the dev server /
proxy (`./scripts/dev.sh`). For a static build, set `VITE_API_BASE_URL`.

### `no such table: companies` / `employees`
The database wasn't migrated. `dev.sh` and `reset.sh` migrate automatically; to do
it manually run `./scripts/migrate.sh` then `./scripts/seed.sh`.

### Login fails / 401 everywhere
The database may be empty (no seeded users) or your token expired. Run
`./scripts/seed.sh`, then sign in with `wes-emp-001@wes.studio` / `WesOs2026!`.

### 403 Forbidden after signing in
Expected for lower roles on restricted actions (RBAC). Only Founder has full
access; see [implementation/auth.md](../implementation/auth.md) for the matrix.

### Port already in use (8000 or 5173)
Another process holds the port. `./scripts/stop.sh` stops WES processes. To find
another owner: `lsof -nP -iTCP:5173 -sTCP:LISTEN`.

### Backend fails to start
Check `logs/backend.log`. Common causes: missing dependencies
(`./scripts/bootstrap.sh`) or a bad `WES_DATABASE_URL`.

### Frontend fails to start
Check `logs/frontend.log`. Usually missing `node_modules` — run
`./scripts/bootstrap.sh` (or `cd frontend && npm install`).

### `localhost` vs `127.0.0.1`
The dev proxy targets `127.0.0.1:8000` to avoid IPv6/IPv4 resolution issues with
`localhost`. Keep the backend on `127.0.0.1`.

### macOS bash
The scripts target macOS's bash 3.2 and require `curl`, `lsof`, and `python3`.

## Where to look

| Symptom | Log |
|---------|-----|
| Backend errors | `logs/backend.log` |
| Frontend errors | `logs/frontend.log` |
| Migration/seed | `logs/startup.log` |
| Health result | `logs/health-report.txt` |

## Still stuck?

```bash
./scripts/health.sh        # see exactly which check fails
./scripts/reset.sh         # clean slate
./scripts/bootstrap.sh     # reinstall dependencies
```
