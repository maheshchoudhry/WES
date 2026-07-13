#!/usr/bin/env bash
# WES OS — shared shell library for the developer scripts.
# Sourced by every script in scripts/. Compatible with macOS bash 3.2.

# --- Paths -----------------------------------------------------------------
# PROJECT_ROOT is the repository root (parent of scripts/).
_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${_LIB_DIR}/../.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
LOG_DIR="${PROJECT_ROOT}/logs"
VENV_DIR="${PROJECT_ROOT}/.venv"
VENV_PY="${VENV_DIR}/bin/python"
VENV_BIN="${VENV_DIR}/bin"

# --- Configuration ---------------------------------------------------------
BACKEND_HOST="127.0.0.1"
BACKEND_PORT="8000"
FRONTEND_PORT="5173"
BACKEND_URL="http://${BACKEND_HOST}:${BACKEND_PORT}"
FRONTEND_URL="http://localhost:${FRONTEND_PORT}"
SWAGGER_URL="${BACKEND_URL}/docs"
API="${BACKEND_URL}/api/v1"

# Dev database (absolute path so it is identical no matter the working dir).
DEV_DB_FILE="${BACKEND_DIR}/wes_os.db"

# Seeded development credentials (Sprint 04).
DEV_EMAIL="wes-emp-001@wes.studio"
DEV_PASSWORD="WesOs2026!"

# Minimum tool versions.
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=11
MIN_NODE_MAJOR=18

# PID files.
BACKEND_PID="${LOG_DIR}/backend.pid"
FRONTEND_PID="${LOG_DIR}/frontend.pid"

# --- Runtime environment ---------------------------------------------------
# Exported so the backend, alembic, and seed all use the same database and so the
# scripts control migration/seeding explicitly (idempotent app auto-init off).
export WES_DATABASE_URL="sqlite:///${DEV_DB_FILE}"
export WES_JWT_SECRET="${WES_JWT_SECRET:-dev-local-secret}"
export WES_AUTO_MIGRATE="false"
export WES_SEED_ON_START="false"

# --- Colored logging -------------------------------------------------------
if [ -t 1 ]; then
  C_RESET="\033[0m"; C_RED="\033[31m"; C_GRN="\033[32m"; C_YEL="\033[33m"
  C_BLU="\033[34m"; C_CYA="\033[36m"; C_BOLD="\033[1m"
else
  C_RESET=""; C_RED=""; C_GRN=""; C_YEL=""; C_BLU=""; C_CYA=""; C_BOLD=""
fi

log_step() { printf "${C_BLU}${C_BOLD}==>${C_RESET} %s\n" "$*"; }
log_ok()   { printf "  ${C_GRN}\xE2\x9C\x93${C_RESET} %s\n" "$*"; }
log_warn() { printf "  ${C_YEL}!${C_RESET} %s\n" "$*"; }
log_err()  { printf "  ${C_RED}\xE2\x9C\x97${C_RESET} %s\n" "$*" >&2; }
log_info() { printf "  %s\n" "$*"; }
die()      { log_err "$*"; exit 1; }

ensure_log_dir() { mkdir -p "$LOG_DIR"; }

# --- Version helpers -------------------------------------------------------
# ver_ge MAJOR MINOR NEEDED_MAJOR NEEDED_MINOR -> 0 if (MAJOR.MINOR) >= needed
ver_ge() {
  if [ "$1" -gt "$3" ]; then return 0; fi
  if [ "$1" -lt "$3" ]; then return 1; fi
  [ "$2" -ge "$4" ]
}

# --- Command / port helpers ------------------------------------------------
have_cmd() { command -v "$1" >/dev/null 2>&1; }

port_in_use() { lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }

# Wait until an HTTP URL returns any response (default 30s). Returns 0 on success.
wait_for_http() {
  local url="$1" timeout="${2:-30}" i=0
  while [ "$i" -lt "$timeout" ]; do
    if curl -s -o /dev/null "$url" 2>/dev/null; then return 0; fi
    sleep 1; i=$((i + 1))
  done
  return 1
}

# HTTP status code for a request. Usage: http_status METHOD URL [TOKEN] [JSON_BODY]
http_status() {
  local method="$1" url="$2" token="${3:-}" body="${4:-}"
  set -- -s -o /dev/null -w "%{http_code}" -X "$method"
  if [ -n "$token" ]; then set -- "$@" -H "Authorization: Bearer $token"; fi
  if [ -n "$body" ]; then set -- "$@" -H "Content-Type: application/json" -d "$body"; fi
  curl "$@" "$url" 2>/dev/null
}

# --- Process management ----------------------------------------------------
pid_alive() { [ -n "$1" ] && kill -0 "$1" >/dev/null 2>&1; }

read_pid() { [ -f "$1" ] && cat "$1" 2>/dev/null || echo ""; }

start_backend() {
  ensure_log_dir
  log_step "Starting backend ($BACKEND_URL)"
  ( cd "$BACKEND_DIR" && nohup "$VENV_BIN/uvicorn" app.main:app \
      --host "$BACKEND_HOST" --port "$BACKEND_PORT" \
      >>"$LOG_DIR/backend.log" 2>&1 & echo $! >"$BACKEND_PID" )
  if wait_for_http "$API/health" 30; then
    log_ok "Backend healthy"
  else
    log_err "Backend failed to become healthy (see logs/backend.log)"
    return 1
  fi
}

start_frontend() {
  ensure_log_dir
  log_step "Starting frontend ($FRONTEND_URL)"
  ( cd "$FRONTEND_DIR" && nohup npm run dev -- --port "$FRONTEND_PORT" --strictPort \
      >>"$LOG_DIR/frontend.log" 2>&1 & echo $! >"$FRONTEND_PID" )
  if wait_for_http "$FRONTEND_URL" 40; then
    log_ok "Frontend serving"
  else
    log_err "Frontend failed to start (see logs/frontend.log)"
    return 1
  fi
}

stop_services() {
  local stopped=0
  local bpid fpid
  bpid="$(read_pid "$BACKEND_PID")"
  fpid="$(read_pid "$FRONTEND_PID")"
  if pid_alive "$bpid"; then kill "$bpid" 2>/dev/null; stopped=1; fi
  if pid_alive "$fpid"; then kill "$fpid" 2>/dev/null; stopped=1; fi
  # Fallbacks in case pids drifted (dev servers spawn children).
  pkill -f "uvicorn app.main:app" >/dev/null 2>&1 && stopped=1
  pkill -f "vite" >/dev/null 2>&1 && stopped=1
  rm -f "$BACKEND_PID" "$FRONTEND_PID"
  sleep 1
  return 0
}

# --- Database helpers ------------------------------------------------------
run_migrations() {
  log_step "Running database migrations"
  ( cd "$BACKEND_DIR" && "$VENV_BIN/alembic" upgrade head >>"$LOG_DIR/startup.log" 2>&1 ) \
    && log_ok "Migrations at head" || { log_err "Migration failed"; return 1; }
}

run_seed() {
  log_step "Seeding database (idempotent)"
  ( cd "$BACKEND_DIR" && "$VENV_PY" -m app.db.seed >>"$LOG_DIR/startup.log" 2>&1 ) \
    && log_ok "Seed ensured" || { log_err "Seed failed"; return 1; }
}

db_employee_count() {
  "$VENV_PY" - "$DEV_DB_FILE" <<'PY' 2>/dev/null
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1])
    print(c.execute("select count(*) from employees").fetchone()[0])
except Exception:
    print(-1)
PY
}

# --- Environment validation ------------------------------------------------
# Verifies the developer's toolchain. Returns non-zero if a required tool is
# missing or too old. Docker is optional (a warning only).
check_environment() {
  local ok=0

  log_step "Validating environment"

  # Python (prefer the venv interpreter, else python3).
  local py="$VENV_PY"
  [ -x "$py" ] || py="$(command -v python3 || true)"
  if [ -n "$py" ] && [ -x "$py" ] || have_cmd python3; then
    [ -x "$py" ] || py="python3"
    local pv major minor
    pv="$("$py" -c 'import sys;print("%d %d"%sys.version_info[:2])' 2>/dev/null)"
    major="$(echo "$pv" | awk '{print $1}')"; minor="$(echo "$pv" | awk '{print $2}')"
    if [ -n "$major" ] && ver_ge "$major" "$minor" "$MIN_PYTHON_MAJOR" "$MIN_PYTHON_MINOR"; then
      log_ok "Python ${major}.${minor}"
    else
      log_err "Python ${major:-?}.${minor:-?} (need >= ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR})"; ok=1
    fi
  else
    log_err "Python 3 not found"; ok=1
  fi

  # Node.
  if have_cmd node; then
    local nmajor
    nmajor="$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null)"
    if [ -n "$nmajor" ] && [ "$nmajor" -ge "$MIN_NODE_MAJOR" ]; then
      log_ok "Node $(node -v)"
    else
      log_err "Node $(node -v 2>/dev/null) (need >= ${MIN_NODE_MAJOR})"; ok=1
    fi
  else
    log_err "Node not found"; ok=1
  fi

  have_cmd npm && log_ok "npm $(npm -v)" || { log_err "npm not found"; ok=1; }
  have_cmd git && log_ok "git $(git --version | awk '{print $3}')" || { log_err "git not found"; ok=1; }
  have_cmd docker && log_ok "docker present (optional)" || log_warn "docker not found (optional)"

  # Virtual environment.
  if [ -x "$VENV_PY" ]; then log_ok "virtualenv present (.venv)"; else log_warn "virtualenv missing (run bootstrap.sh)"; fi

  # Ports.
  local p
  for p in "$BACKEND_PORT" "$FRONTEND_PORT"; do
    if port_in_use "$p"; then log_warn "port $p in use (dev/stop will manage it)"; else log_ok "port $p free"; fi
  done

  return "$ok"
}

# --- Dependency / env bootstrapping ---------------------------------------
ensure_env_files() {
  log_step "Ensuring .env files"
  local pair
  for pair in "${PROJECT_ROOT}/.env" "${BACKEND_DIR}/.env" "${FRONTEND_DIR}/.env"; do
    if [ ! -f "$pair" ] && [ -f "${pair}.example" ]; then
      cp "${pair}.example" "$pair"
      log_ok "created ${pair#$PROJECT_ROOT/}"
    else
      log_info "${pair#$PROJECT_ROOT/} present"
    fi
  done
}

ensure_backend_deps() {
  log_step "Ensuring backend dependencies"
  if [ ! -x "$VENV_PY" ]; then
    log_info "creating virtualenv (.venv)"
    python3 -m venv "$VENV_DIR" || return 1
  fi
  if [ ! -x "$VENV_BIN/uvicorn" ] || [ "${FORCE_INSTALL:-0}" = "1" ]; then
    log_info "installing backend packages (pip)"
    "$VENV_BIN/pip" install -q --upgrade pip >/dev/null 2>&1 || true
    "$VENV_BIN/pip" install -q -r "${BACKEND_DIR}/requirements.txt" || return 1
  fi
  log_ok "backend dependencies ready"
}

ensure_frontend_deps() {
  log_step "Ensuring frontend dependencies"
  if [ ! -d "${FRONTEND_DIR}/node_modules" ] || [ "${FORCE_INSTALL:-0}" = "1" ]; then
    log_info "installing frontend packages (npm)"
    ( cd "$FRONTEND_DIR" && npm install --no-audit --no-fund ) || return 1
  fi
  log_ok "frontend dependencies ready"
}

# --- Authentication + health report ---------------------------------------
login_token() {
  local resp
  resp="$(curl -s -X POST "$API/auth/login" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$DEV_EMAIL\",\"password\":\"$DEV_PASSWORD\"}" 2>/dev/null)"
  WES_RESP="$resp" "$VENV_PY" -c "import os,json
try:
    print(json.loads(os.environ['WES_RESP'])['data']['tokens']['access_token'])
except Exception:
    print('')"
}

# Runs the full health check, prints a report, writes logs/health-report.txt,
# and returns the number of failed checks (0 == healthy).
wes_health_report() {
  ensure_log_dir
  local report="${LOG_DIR}/health-report.txt"
  local fails=0 code token
  : >"$report"

  _hcheck() { # label actual want
    if [ "$2" = "$3" ]; then
      log_ok "$1 ($2)"; echo "PASS  $1 ($2)" >>"$report"
    else
      log_err "$1 (got $2, want $3)"; echo "FAIL  $1 (got $2 want $3)" >>"$report"
      fails=$((fails + 1))
    fi
  }

  log_step "Health checks"
  code="$(http_status GET "$API/health")";               _hcheck "Backend running" "$code" "200"
  code="$(http_status GET "$FRONTEND_URL")";              _hcheck "Frontend running" "$code" "200"
  code="$(http_status GET "$API/health/ready")";          _hcheck "Database connected" "$code" "200"

  token="$(login_token)"
  if [ -n "$token" ]; then
    log_ok "Authentication working (login 200)"; echo "PASS  Authentication (login)" >>"$report"
  else
    log_err "Authentication failed (login)"; echo "FAIL  Authentication (login)" >>"$report"
    fails=$((fails + 1))
  fi
  code="$(http_status GET "$API/auth/me" "$token")";      _hcheck "JWT working (/auth/me)" "$code" "200"
  code="$(http_status GET "$API/dashboard/stats" "$token")"; _hcheck "Dashboard API" "$code" "200"
  code="$(http_status GET "$API/companies" "$token")";    _hcheck "Company API" "$code" "200"
  code="$(http_status GET "$API/departments" "$token")";  _hcheck "Departments API" "$code" "200"
  code="$(http_status GET "$API/employees" "$token")";    _hcheck "Employees API" "$code" "200"
  code="$(http_status GET "$API/dashboard/stats")";       _hcheck "Unauthorized -> 401" "$code" "401"

  {
    echo ""
    if [ "$fails" -eq 0 ]; then echo "RESULT: ALL CHECKS PASSED"; else echo "RESULT: ${fails} CHECK(S) FAILED"; fi
  } >>"$report"
  return "$fails"
}

print_urls() {
  printf "\n${C_BOLD}WES OS is running:${C_RESET}\n"
  printf "  ${C_CYA}Backend${C_RESET}   %s\n" "$BACKEND_URL"
  printf "  ${C_CYA}Swagger${C_RESET}   %s\n" "$SWAGGER_URL"
  printf "  ${C_CYA}Frontend${C_RESET}  %s\n" "$FRONTEND_URL"
  printf "\n  Sign in: %s / %s\n" "$DEV_EMAIL" "$DEV_PASSWORD"
  printf "  Stop:    ./scripts/stop.sh\n\n"
}
