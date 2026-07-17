#!/usr/bin/env bash
#
# WES OS backup — PostgreSQL logical dump + Redis snapshot, with retention.
# Invoked by wes-backup.timer (daily). Reads creds from /opt/wes/.env.
set -euo pipefail

ENV_FILE="/opt/wes/.env"
BACKUP_DIR="/opt/backups"
LOG="/opt/logs/backup.log"
RETENTION_DAYS="${WES_BACKUP_RETENTION_DAYS:-14}"
STAMP="$(date +%Y%m%d-%H%M%S)"

# shellcheck disable=SC1090
[ -f "${ENV_FILE}" ] && set -a && . "${ENV_FILE}" && set +a

log() { printf '%s %s\n' "$(date -Is)" "$*" | tee -a "${LOG}"; }

log "backup start ${STAMP}"

# 1. PostgreSQL — compressed logical dump.
pg_out="${BACKUP_DIR}/postgres/wes_os-${STAMP}.sql.gz"
if docker exec -e PGPASSWORD="${POSTGRES_PASSWORD:-}" wes-postgres \
     pg_dump -U "${POSTGRES_USER:-wes}" -d "${POSTGRES_DB:-wes_os}" \
   | gzip > "${pg_out}"; then
  log "postgres dump -> ${pg_out} ($(du -h "${pg_out}" | cut -f1))"
else
  log "ERROR: postgres dump failed"; exit 1
fi

# 2. Redis — trigger a save and copy the RDB snapshot.
if docker exec wes-redis redis-cli SAVE >/dev/null 2>&1; then
  redis_out="${BACKUP_DIR}/redis/dump-${STAMP}.rdb"
  docker cp wes-redis:/data/dump.rdb "${redis_out}" 2>/dev/null \
    && log "redis snapshot -> ${redis_out}" \
    || log "WARN: redis snapshot copy skipped"
else
  log "WARN: redis SAVE failed"
fi

# 3. Retention — prune backups older than RETENTION_DAYS.
find "${BACKUP_DIR}/postgres" -name 'wes_os-*.sql.gz' -mtime +"${RETENTION_DAYS}" -delete
find "${BACKUP_DIR}/redis"    -name 'dump-*.rdb'      -mtime +"${RETENTION_DAYS}" -delete

log "backup done; retention ${RETENTION_DAYS}d applied"
