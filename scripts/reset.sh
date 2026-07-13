#!/usr/bin/env bash
# Reset the development environment: stop, wipe the database, migrate, seed, restart.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

ensure_log_dir
printf "${C_BOLD}WES OS — Reset Environment${C_RESET}\n\n"

log_step "Stopping services"
stop_services
log_ok "stopped"

log_step "Deleting development database"
rm -f "$DEV_DB_FILE"
log_ok "removed $(basename "$DEV_DB_FILE")"

run_migrations || die "Migrations failed"
run_seed || die "Seed failed"

start_backend || die "Backend did not start"
start_frontend || die "Frontend did not start"

if wes_health_report; then
  print_urls
  log_ok "Environment reset and fully operational."
  exit 0
else
  log_err "Reset completed but health checks failed (see logs/health-report.txt)."
  exit 1
fi
