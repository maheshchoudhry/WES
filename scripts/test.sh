#!/usr/bin/env bash
# Run the full test suite (backend pytest + frontend vitest).
set -uo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

printf "${C_BOLD}WES OS — Tests${C_RESET}\n\n"
rc=0

log_step "Backend tests (pytest)"
( cd "$BACKEND_DIR" && "$VENV_PY" -m pytest -q )
if [ $? -eq 0 ]; then log_ok "backend tests passed"; else log_err "backend tests failed"; rc=1; fi

log_step "Frontend tests (vitest)"
( cd "$FRONTEND_DIR" && npm run test --silent )
if [ $? -eq 0 ]; then log_ok "frontend tests passed"; else log_err "frontend tests failed"; rc=1; fi

echo ""
[ "$rc" -eq 0 ] && log_ok "All tests passed" || log_err "Some tests failed"
exit "$rc"
