#!/usr/bin/env bash
# Verify a running WES OS: backend, frontend, database, JWT, auth, and every API.
# Exit code 0 = healthy, non-zero = number of failed checks.
set -uo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"

printf "${C_BOLD}WES OS — Health Check${C_RESET}\n\n"

wes_health_report
result=$?

echo ""
if [ "$result" -eq 0 ]; then
  log_ok "All systems healthy. Report: logs/health-report.txt"
else
  log_err "${result} check(s) failed. Report: logs/health-report.txt"
fi
exit "$result"
