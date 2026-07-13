#!/usr/bin/env bash
# One-command development startup for WES OS.
#
# Validates the environment, ensures dependencies and .env files, migrates and
# seeds the database, starts the backend and frontend, and verifies the whole
# stack with health checks.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

ensure_log_dir
: >"${LOG_DIR}/startup.log"

printf "${C_BOLD}WES OS — Development Startup${C_RESET}\n\n"

check_environment || die "Environment validation failed. Run ./scripts/bootstrap.sh"
ensure_env_files
ensure_backend_deps || die "Failed to prepare backend dependencies"
ensure_frontend_deps || die "Failed to prepare frontend dependencies"

# Clean slate so ports and pids are deterministic.
log_step "Stopping any running services"
stop_services
log_ok "clean"

run_migrations || die "Migrations failed"

# Seed the database (idempotent — only inserts when empty).
count="$(db_employee_count)"
if [ "$count" -le 0 ]; then log_info "database empty — seeding"; else log_info "database has ${count} employees"; fi
run_seed || die "Seed failed"

start_backend || die "Backend did not start"
start_frontend || die "Frontend did not start"

if wes_health_report; then
  print_urls
  log_ok "WES OS is fully operational."
  exit 0
else
  log_err "Startup completed but health checks failed (see logs/health-report.txt)."
  exit 1
fi
