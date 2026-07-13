#!/usr/bin/env bash
# Auto-format the codebase (backend: ruff --fix + black; frontend: prettier --write).
set -uo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

printf "${C_BOLD}WES OS — Format${C_RESET}\n\n"

log_step "Backend: ruff --fix"
( cd "$BACKEND_DIR" && "$VENV_BIN/ruff" check --fix app tests ) && log_ok "ruff applied" || log_warn "ruff reported remaining issues"

log_step "Backend: black"
( cd "$BACKEND_DIR" && "$VENV_BIN/black" --quiet app tests ) && log_ok "black formatted"

log_step "Frontend: prettier --write"
( cd "$FRONTEND_DIR" && npm run format --silent ) && log_ok "prettier formatted"

echo ""
log_ok "Formatting complete"
