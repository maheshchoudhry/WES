#!/usr/bin/env bash
# Seed the WES organization (idempotent).
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
ensure_log_dir
run_seed
count="$(db_employee_count)"
log_info "Employees in database: ${count}"
