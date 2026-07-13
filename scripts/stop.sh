#!/usr/bin/env bash
# Stop the backend and frontend.
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib/common.sh"
log_step "Stopping WES OS services"
stop_services
log_ok "Services stopped"
