#!/usr/bin/env bash
#
# WES OS — VPS bootstrap for Ubuntu 24.04 (Noble).
#
# Prepares a fresh server to host WES OS: Docker, Git, containerized PostgreSQL +
# Redis on a dedicated Docker network, Nginx reverse proxy (HTTPS-ready), UFW,
# Fail2ban, Certbot, Python, Node.js, systemd units, log rotation, backups, and
# monitoring. It does NOT deploy the WES application — it only prepares the host.
#
# Idempotent: safe to re-run. Run as root:
#     sudo bash bootstrap.sh
#
# Optional environment overrides:
#     WES_DOMAIN=wes.example.com   # server_name for Nginx / certbot
#     WES_ADMIN_EMAIL=you@x.com    # certbot registration email
#     NODE_MAJOR=20                # Node.js major version
#     WES_SSH_PORT=22              # SSH port to allow through UFW
set -euo pipefail

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
WES_DOMAIN="${WES_DOMAIN:-_}"
WES_ADMIN_EMAIL="${WES_ADMIN_EMAIL:-admin@example.com}"
NODE_MAJOR="${NODE_MAJOR:-20}"
WES_SSH_PORT="${WES_SSH_PORT:-22}"
PG_VERSION="16"
REDIS_VERSION="7"
DOCKER_NET="wes-net"

WES_DIR="/opt/wes"
BACKUP_DIR="/opt/backups"
LOG_DIR="/opt/logs"
CONF_DIR="${WES_DIR}/config"
ENV_FILE="${WES_DIR}/.env"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log()  { printf '\033[0;36m[bootstrap]\033[0m %s\n' "$*"; }
ok()   { printf '\033[0;32m[  ok  ]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[ warn ]\033[0m %s\n' "$*"; }
die()  { printf '\033[0;31m[ fail ]\033[0m %s\n' "$*" >&2; exit 1; }

require_root() { [ "$(id -u)" -eq 0 ] || die "Run as root: sudo bash bootstrap.sh"; }

require_ubuntu() {
  [ -r /etc/os-release ] || die "Cannot read /etc/os-release"
  . /etc/os-release
  [ "${ID:-}" = "ubuntu" ] || die "This bootstrap targets Ubuntu (found: ${ID:-unknown})"
  case "${VERSION_ID:-}" in
    24.04|24.10|22.04) ok "Ubuntu ${VERSION_ID} detected" ;;
    *) warn "Tested on 24.04; found ${VERSION_ID:-unknown} — continuing" ;;
  esac
}

# --------------------------------------------------------------------------- #
# Steps
# --------------------------------------------------------------------------- #
step_folders() {
  log "Creating directory layout"
  mkdir -p "${WES_DIR}" "${BACKUP_DIR}" "${LOG_DIR}" "${CONF_DIR}" \
           "${WES_DIR}/www" "${BACKUP_DIR}/postgres" "${BACKUP_DIR}/redis"
  chmod 750 "${BACKUP_DIR}"
  ok "Folders: ${WES_DIR}, ${BACKUP_DIR}, ${LOG_DIR}"
}

step_apt_base() {
  log "Updating apt and installing base packages"
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg lsb-release git ufw fail2ban nginx certbot \
    python3 python3-venv python3-pip "postgresql-client-${PG_VERSION}" redis-tools \
    jq unzip logrotate apt-transport-https software-properties-common
  ok "Base packages installed (git, nginx, ufw, fail2ban, certbot, python3, clients)"
}

step_docker() {
  if command -v docker >/dev/null 2>&1; then ok "Docker already installed"; else
    log "Installing Docker Engine + Compose plugin (official repo)"
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
      > /etc/apt/sources.list.d/docker.list
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io \
      docker-buildx-plugin docker-compose-plugin
  fi
  systemctl enable --now docker
  # Dedicated bridge network for WES services.
  docker network inspect "${DOCKER_NET}" >/dev/null 2>&1 \
    || docker network create "${DOCKER_NET}"
  ok "Docker ready; network '${DOCKER_NET}' present"
}

step_nodejs() {
  if command -v node >/dev/null 2>&1 \
     && [ "$(node -v | sed 's/^v\([0-9]*\).*/\1/')" -ge "${NODE_MAJOR}" ]; then
    ok "Node.js $(node -v) already installed"
  else
    log "Installing Node.js ${NODE_MAJOR}.x (NodeSource)"
    curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash -
    apt-get install -y nodejs
  fi
  ok "Node.js $(node -v), npm $(npm -v)"
}

step_env() {
  if [ -f "${ENV_FILE}" ]; then ok ".env already present (secrets preserved)"; return; fi
  log "Generating ${ENV_FILE} with fresh secrets"
  local db_pass jwt_secret secret_key
  db_pass="$(openssl rand -hex 24)"
  jwt_secret="$(openssl rand -hex 32)"
  secret_key="$(openssl rand -hex 32)"
  sed -e "s|__DB_PASSWORD__|${db_pass}|" \
      -e "s|__JWT_SECRET__|${jwt_secret}|" \
      -e "s|__SECRET_KEY__|${secret_key}|" \
      -e "s|__DOMAIN__|${WES_DOMAIN}|" \
      "${HERE}/config/wes.env.example" > "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  ok "Secrets generated (chmod 600). DB/JWT/secret keys are unique to this host."
}

step_infra_stack() {
  log "Installing containerized PostgreSQL ${PG_VERSION} + Redis ${REDIS_VERSION}"
  cp "${HERE}/config/docker-compose.infra.yml" "${CONF_DIR}/docker-compose.infra.yml"
  ( cd "${CONF_DIR}" && docker compose --env-file "${ENV_FILE}" \
      -f docker-compose.infra.yml -p wes-infra up -d )
  ok "PostgreSQL + Redis containers started on '${DOCKER_NET}' (restart=unless-stopped)"
}

step_nginx() {
  log "Configuring Nginx reverse proxy (HTTPS-ready)"
  # Holding page until WES is deployed.
  cp "${HERE}/config/maintenance.html" "${WES_DIR}/www/index.html"
  local site="/etc/nginx/sites-available/wes"
  sed "s/__DOMAIN__/${WES_DOMAIN}/g" "${HERE}/config/nginx-wes.conf" > "${site}"
  ln -sf "${site}" /etc/nginx/sites-enabled/wes
  rm -f /etc/nginx/sites-enabled/default
  nginx -t
  systemctl enable --now nginx
  systemctl reload nginx
  ok "Nginx active; reverse proxy → 127.0.0.1:8000 (/api) + static (/). Certbot-ready."
}

step_firewall() {
  log "Configuring UFW firewall"
  ufw --force reset >/dev/null
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow "${WES_SSH_PORT}"/tcp
  ufw allow 80/tcp
  ufw allow 443/tcp
  ufw --force enable
  ok "UFW enabled: allow ${WES_SSH_PORT}(ssh), 80, 443; deny the rest"
}

step_fail2ban() {
  log "Configuring Fail2ban"
  sed "s/__SSH_PORT__/${WES_SSH_PORT}/g" "${HERE}/config/fail2ban-jail.local" \
    > /etc/fail2ban/jail.local
  systemctl enable --now fail2ban
  systemctl restart fail2ban
  ok "Fail2ban active (sshd + nginx jails)"
}

step_logrotate() {
  log "Installing log rotation"
  cp "${HERE}/config/logrotate-wes" /etc/logrotate.d/wes
  ok "Logrotate configured for ${LOG_DIR}/*.log (14d, compressed)"
}

step_systemd() {
  log "Installing systemd units (auto-restart, backups, health checks)"
  for unit in wes-infra.service wes-backup.service wes-backup.timer \
              wes-healthcheck.service wes-healthcheck.timer; do
    cp "${HERE}/config/systemd/${unit}" "/etc/systemd/system/${unit}"
  done
  install -m 0755 "${HERE}/scripts/backup.sh"      "${WES_DIR}/backup.sh"
  install -m 0755 "${HERE}/scripts/healthcheck.sh" "${WES_DIR}/healthcheck.sh"
  install -m 0755 "${HERE}/verify.sh"              "${WES_DIR}/verify.sh"
  systemctl daemon-reload
  systemctl enable --now wes-infra.service
  systemctl enable --now wes-backup.timer
  systemctl enable --now wes-healthcheck.timer
  ok "systemd: wes-infra (boot), wes-backup.timer (daily), wes-healthcheck.timer (5m)"
}

step_verify() {
  log "Runtime verification"
  bash "${WES_DIR}/verify.sh"
}

# --------------------------------------------------------------------------- #
main() {
  require_root
  require_ubuntu
  step_folders
  step_apt_base
  step_docker
  step_nodejs
  step_env
  step_infra_stack
  step_nginx
  step_firewall
  step_fail2ban
  step_logrotate
  step_systemd
  step_verify
  echo
  ok "WES OS server preparation complete. WES is NOT deployed (as requested)."
  log "Next: point DNS at this host, run 'certbot --nginx -d ${WES_DOMAIN}' for HTTPS,"
  log "      then deploy WES OS into ${WES_DIR}. See deploy/vps/SERVER_SETUP.md."
}

main "$@"
