#!/usr/bin/env bash
#
# WES OS monitoring probe — invoked by wes-healthcheck.timer every 5 minutes.
# Writes a structured status line to /opt/logs/health.log and exits non-zero if
# any critical component is down (so `systemctl status wes-healthcheck` surfaces
# failures and journald/alerting can pick them up).
set -uo pipefail

LOG="/opt/logs/health.log"
ts="$(date -Is)"
status="ok"; problems=()

_check() { # _check name test-cmd...
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then :; else status="degraded"; problems+=("$name"); fi
}

_check docker        systemctl is-active --quiet docker
_check nginx         systemctl is-active --quiet nginx
_check fail2ban      systemctl is-active --quiet fail2ban
_check postgres      docker exec wes-postgres pg_isready -q
_check redis         bash -c "docker exec wes-redis redis-cli ping | grep -q PONG"
_check http          bash -c "curl -fsS -o /dev/null http://127.0.0.1/healthz"
_check disk          bash -c "[ \"\$(df -P /opt | awk 'NR==2{print \$5+0}')\" -lt 90 ]"

if [ "${#problems[@]}" -eq 0 ]; then
  printf '%s health=%s\n' "${ts}" "${status}" >> "${LOG}"
  exit 0
else
  printf '%s health=%s problems=%s\n' "${ts}" "${status}" "${problems[*]}" >> "${LOG}"
  exit 1
fi
