#!/usr/bin/env bash
# Apply database migrations to head.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
ensure_log_dir
run_migrations
