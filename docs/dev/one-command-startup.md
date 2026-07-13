# One-Command Startup

WES OS runs from a single command. No manual backend/frontend/migration/seed steps.

## Start everything

```bash
./scripts/dev.sh
```

This automatically:

1. ✓ checks Python, Node, npm, Git (Docker optional)
2. ✓ verifies / creates the virtualenv and installs backend packages
3. ✓ installs frontend packages
4. ✓ creates `.env` files from the examples
5. ✓ frees the ports (stops anything already running)
6. ✓ runs database migrations
7. ✓ seeds the database if empty
8. ✓ starts the backend
9. ✓ starts the frontend
10. ✓ verifies APIs + authentication with health checks
11. ✓ prints the URLs

When it finishes you'll see:

```
WES OS is running:
  Backend   http://127.0.0.1:8000
  Swagger   http://127.0.0.1:8000/docs
  Frontend  http://localhost:5173

  Sign in: wes-emp-001@wes.studio / WesOs2026!
```

`dev.sh` exits `0` only when every health check passes.

## Stop everything

```bash
./scripts/stop.sh
```

## Reset everything (fresh database)

```bash
./scripts/reset.sh
```

Stops services, deletes the dev database, re-migrates, re-seeds, and restarts —
then verifies health.

## Check health at any time

```bash
./scripts/health.sh
```

Exit code `0` = healthy; otherwise the number of failed checks. A report is
written to `logs/health-report.txt`.
