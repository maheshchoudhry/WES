#!/usr/bin/env bash
# One-command bootstrap for a fresh clone: install everything and prepare the DB.
#
#   git clone <repo> && cd WES && ./scripts/bootstrap.sh && ./scripts/dev.sh
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

ensure_log_dir
printf "${C_BOLD}WES OS — Bootstrap${C_RESET}\n\n"

# Required toolchain (python/node/npm/git). Missing venv/ports are fine here.
if ! check_environment; then
  die "Missing required tools. Install Python 3.11+, Node 18+, npm and git, then re-run."
fi

ensure_env_files
ensure_backend_deps || die "Backend dependency installation failed"
ensure_frontend_deps || die "Frontend dependency installation failed"

run_migrations || die "Migrations failed"
run_seed || die "Seed failed"

log_step "Verifying installation"
( cd "$BACKEND_DIR" && "$VENV_PY" -c "import app.main" ) >/dev/null 2>&1 \
  && log_ok "backend imports" || die "backend import failed"
[ -d "${FRONTEND_DIR}/node_modules" ] && log_ok "frontend packages installed" || die "node_modules missing"
count="$(db_employee_count)"
[ "$count" -ge 1 ] && log_ok "database seeded (${count} employees)" || die "database not seeded"

printf "\n${C_GRN}${C_BOLD}Bootstrap complete.${C_RESET} Start WES OS with:\n\n  ./scripts/dev.sh\n\n"
