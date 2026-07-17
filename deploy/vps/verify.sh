#!/usr/bin/env bash
#
# WES OS — server verification. Runs on the VPS after bootstrap to prove every
# component is installed, running, and reachable. Exit code is non-zero if any
# required check fails. Safe to run any time (read-only).
set -uo pipefail

WES_DIR="/opt/wes"
ENV_FILE="${WES_DIR}/.env"
DOCKER_NET="wes-net"
PASS=0; FAIL=0

green() { printf '\033[0;32m PASS \033[0m %s\n' "$*"; PASS=$((PASS+1)); }
red()   { printf '\033[0;31m FAIL \033[0m %s\n' "$*"; FAIL=$((FAIL+1)); }
info()  { printf '\033[0;36m----- \033[0m %s\n' "$*"; }

check() { # check "desc" cmd...
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then green "$desc"; else red "$desc"; fi
}

# Load env (DB creds) if present.
# shellcheck disable=SC1090
[ -f "${ENV_FILE}" ] && set -a && . "${ENV_FILE}" && set +a

info "Toolchain"
check "docker installed"            docker --version
check "docker compose plugin"       docker compose version
check "git installed"               git --version
check "python3 installed"           python3 --version
check "node installed"              node --version
check "npm installed"               npm --version
check "certbot installed"           certbot --version
check "psql client installed"       psql --version
check "redis-cli installed"         redis-cli --version

info "Services (systemd)"
check "docker active"               systemctl is-active --quiet docker
check "nginx active"                systemctl is-active --quiet nginx
check "fail2ban active"             systemctl is-active --quiet fail2ban
check "wes-infra enabled"           systemctl is-enabled --quiet wes-infra.service
check "wes-backup.timer active"     systemctl is-active --quiet wes-backup.timer
check "wes-healthcheck.timer active" systemctl is-active --quiet wes-healthcheck.timer

info "Docker network + containers"
check "network ${DOCKER_NET} exists" docker network inspect "${DOCKER_NET}"
check "postgres container up"        bash -c "docker ps --format '{{.Names}}' | grep -q wes-postgres"
check "redis container up"           bash -c "docker ps --format '{{.Names}}' | grep -q wes-redis"

info "PostgreSQL"
if docker exec wes-postgres pg_isready -U "${POSTGRES_USER:-wes}" >/dev/null 2>&1; then
  green "postgres accepting connections"
else red "postgres accepting connections"; fi
if docker exec -e PGPASSWORD="${POSTGRES_PASSWORD:-}" wes-postgres \
     psql -U "${POSTGRES_USER:-wes}" -d "${POSTGRES_DB:-wes_os}" -c "SELECT 1;" >/dev/null 2>&1; then
  green "database ${POSTGRES_DB:-wes_os} reachable"
else red "database ${POSTGRES_DB:-wes_os} reachable"; fi

info "Redis"
if docker exec wes-redis redis-cli ping 2>/dev/null | grep -q PONG; then
  green "redis PONG"; else red "redis PONG"; fi

info "Nginx"
check "nginx config valid"           nginx -t
check "http :80 responds"            bash -c "curl -fsS -o /dev/null http://127.0.0.1/healthz"

info "Firewall"
check "ufw active"                   bash -c "ufw status | grep -q 'Status: active'"

info "Folders"
for d in /opt/wes /opt/backups /opt/logs; do
  check "folder ${d}"                test -d "${d}"
done

echo
info "Result: ${PASS} passed, ${FAIL} failed"
[ "${FAIL}" -eq 0 ] || exit 1
