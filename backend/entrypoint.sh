#!/usr/bin/env sh
# Container entrypoint: apply migrations, optionally seed, then run the given CMD.
set -e

echo "[entrypoint] Applying database migrations…"
alembic upgrade head

if [ "${WES_SEED_ON_START:-false}" = "true" ]; then
  echo "[entrypoint] Seeding development data…"
  python -m app.db.seed
fi

echo "[entrypoint] Starting: $*"
exec "$@"
