#!/usr/bin/env bash
# Lint the codebase (backend: ruff + black --check; frontend: tsc + prettier --check).
set -uo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

printf "${C_BOLD}WES OS — Lint${C_RESET}\n\n"
rc=0

log_step "Backend lint (ruff)"
( cd "$BACKEND_DIR" && "$VENV_BIN/ruff" check app tests ) \
  && log_ok "ruff clean" || { log_err "ruff found issues"; rc=1; }

log_step "Backend format check (black)"
( cd "$BACKEND_DIR" && "$VENV_BIN/black" --check --quiet app tests ) \
  && log_ok "black clean" || { log_err "black would reformat (run ./scripts/format.sh)"; rc=1; }

log_step "Frontend types (tsc)"
( cd "$FRONTEND_DIR" && npm run typecheck --silent ) \
  && log_ok "typecheck clean" || { log_err "type errors"; rc=1; }

log_step "Frontend format check (prettier)"
( cd "$FRONTEND_DIR" && npm run format:check --silent ) \
  && log_ok "prettier clean" || { log_err "prettier would reformat (run ./scripts/format.sh)"; rc=1; }

echo ""
[ "$rc" -eq 0 ] && log_ok "Lint passed" || log_err "Lint found issues"
exit "$rc"
