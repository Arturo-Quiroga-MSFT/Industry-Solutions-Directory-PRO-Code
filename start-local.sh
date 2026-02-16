#!/bin/bash
# ─────────────────────────────────────────────────────────────
# start-local.sh — Start backend + frontend for local dev
# Usage: ./start-local.sh          (start both)
#        ./start-local.sh backend  (backend only)
#        ./start-local.sh frontend (frontend only)
#        ./start-local.sh stop     (kill both)
# ─────────────────────────────────────────────────────────────

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=5173
VENV_DIR="$REPO_ROOT/.venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; }
info() { echo -e "${CYAN}[→]${NC} $1"; }

# ── Port management ──────────────────────────────────────────
free_port() {
  local port=$1
  local pids
  pids=$(lsof -ti:"$port" 2>/dev/null || true)
  if [[ -n "$pids" ]]; then
    warn "Port $port in use (PIDs: $pids) — killing..."
    echo "$pids" | xargs kill -9 2>/dev/null || true
    sleep 1
    log "Port $port freed"
  else
    log "Port $port is available"
  fi
}

# ── Health check ─────────────────────────────────────────────
wait_for_service() {
  local url=$1
  local name=$2
  local max_attempts=30
  local attempt=0
  info "Waiting for $name at $url ..."
  while [[ $attempt -lt $max_attempts ]]; do
    if curl -s -o /dev/null -w '' "$url" 2>/dev/null; then
      log "$name is ready!"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  err "$name failed to start after ${max_attempts}s"
  return 1
}

# ── Start backend ────────────────────────────────────────────
start_backend() {
  echo ""
  echo -e "${CYAN}═══ BACKEND (FastAPI on port $BACKEND_PORT) ═══${NC}"

  # Check venv
  if [[ ! -d "$VENV_DIR" ]]; then
    err "Python venv not found at $VENV_DIR"
    err "Create it first: python3 -m venv .venv && pip install -r frontend-react/backend/requirements.txt"
    return 1
  fi

  free_port "$BACKEND_PORT"

  info "Starting uvicorn..."
  source "$VENV_DIR/bin/activate"
  cd "$REPO_ROOT/frontend-react/backend"
  uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT" --reload \
    > "$REPO_ROOT/logs/backend.log" 2>&1 &
  local pid=$!
  echo "$pid" > "$REPO_ROOT/logs/backend.pid"
  cd "$REPO_ROOT"

  wait_for_service "http://localhost:$BACKEND_PORT/health" "Backend"
  info "Backend PID: $pid | Log: logs/backend.log"
}

# ── Start frontend ───────────────────────────────────────────
start_frontend() {
  echo ""
  echo -e "${CYAN}═══ FRONTEND (Vite on port $FRONTEND_PORT) ═══${NC}"

  free_port "$FRONTEND_PORT"

  info "Starting Vite dev server..."
  cd "$REPO_ROOT/frontend-react"
  npx vite --port "$FRONTEND_PORT" \
    > "$REPO_ROOT/logs/frontend.log" 2>&1 &
  local pid=$!
  echo "$pid" > "$REPO_ROOT/logs/frontend.pid"
  cd "$REPO_ROOT"

  wait_for_service "http://localhost:$FRONTEND_PORT" "Frontend"
  info "Frontend PID: $pid | Log: logs/frontend.log"
}

# ── Stop all ─────────────────────────────────────────────────
stop_all() {
  echo ""
  echo -e "${CYAN}═══ STOPPING SERVICES ═══${NC}"
  free_port "$BACKEND_PORT"
  free_port "$FRONTEND_PORT"
  rm -f "$REPO_ROOT/logs/backend.pid" "$REPO_ROOT/logs/frontend.pid"
  log "All services stopped"
}

# ── Summary ──────────────────────────────────────────────────
print_summary() {
  echo ""
  echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
  echo -e "${GREEN}  Local dev environment is running!${NC}"
  echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
  echo ""
  echo -e "  Backend API:  ${CYAN}http://localhost:$BACKEND_PORT${NC}"
  echo -e "  Health check: ${CYAN}http://localhost:$BACKEND_PORT/health${NC}"
  echo -e "  Frontend:     ${CYAN}http://localhost:$FRONTEND_PORT${NC}"
  echo -e "  Seller mode:  ${CYAN}http://localhost:$FRONTEND_PORT/?mode=seller${NC}"
  echo -e "  Customer mode:${CYAN}http://localhost:$FRONTEND_PORT/?mode=customer${NC}"
  echo ""
  echo -e "  Logs:         ${YELLOW}logs/backend.log${NC}  |  ${YELLOW}logs/frontend.log${NC}"
  echo -e "  Stop:         ${YELLOW}./start-local.sh stop${NC}"
  echo ""
}

# ── Main ─────────────────────────────────────────────────────
mkdir -p "$REPO_ROOT/logs"

case "${1:-all}" in
  backend)
    start_backend
    ;;
  frontend)
    start_frontend
    ;;
  stop)
    stop_all
    ;;
  all)
    start_backend
    start_frontend
    print_summary
    ;;
  *)
    echo "Usage: $0 {all|backend|frontend|stop}"
    exit 1
    ;;
esac
