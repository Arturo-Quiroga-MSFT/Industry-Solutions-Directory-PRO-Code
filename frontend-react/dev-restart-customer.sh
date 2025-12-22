#!/bin/bash

# Quick Start/Restart Script for React App (Frontend + Backend) - CUSTOMER MODE
# Usage: ./dev-restart-customer.sh [frontend|backend|all]
# This script starts the application in CUSTOMER MODE (unbiased, no partner rankings)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRONTEND_DIR="$SCRIPT_DIR"
BACKEND_DIR="$SCRIPT_DIR/backend"

# Process name identifiers
BACKEND_PROCESS="uvicorn"
FRONTEND_PROCESS="vite"

# APP_MODE for this script
APP_MODE="customer"

# Use different ports for customer mode to allow side-by-side testing
BACKEND_PORT=8001
FRONTEND_PORT=5174

print_header() {
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_mode() {
    echo -e "${CYAN}🛡️  CUSTOMER MODE: Unbiased insights, no partner rankings${NC}"
}

# Kill process by port
kill_port() {
    local PORT=$1
    local PROCESS_NAME=$2
    
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_info "Stopping process on port $PORT ($PROCESS_NAME)..."
        lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
        sleep 1
        print_success "Process on port $PORT stopped"
    else
        print_info "No process running on port $PORT"
    fi
}

# Kill process by name pattern
kill_process_by_name() {
    local PATTERN=$1
    local NAME=$2
    
    if pgrep -f "$PATTERN" > /dev/null; then
        print_info "Stopping $NAME processes..."
        pkill -f "$PATTERN" 2>/dev/null || true
        sleep 1
        print_success "$NAME processes stopped"
    else
        print_info "No $NAME processes running"
    fi
}

stop_backend() {
    print_header "Stopping Backend"
    kill_port $BACKEND_PORT "Backend API"
    kill_process_by_name "uvicorn.*main:app.*--port $BACKEND_PORT" "Backend"
}

stop_frontend() {
    print_header "Stopping Frontend"
    kill_port $FRONTEND_PORT "Frontend Dev Server"
    kill_process_by_name "vite.*--port $FRONTEND_PORT" "Frontend"
}

start_backend() {
    print_header "Starting Backend (CUSTOMER MODE)"
    print_mode
    
    # Check if virtual environment exists
    if [ ! -d "$SCRIPT_DIR/../.venv" ]; then
        print_error "Virtual environment not found at $SCRIPT_DIR/../.venv"
        print_info "Please create a virtual environment first"
        exit 1
    fi
    
    cd "$BACKEND_DIR"
    
    # Check if requirements are installed
    if [ ! -f "$BACKEND_DIR/.env" ]; then
        print_error "Backend .env file not found!"
        print_info "Please create backend/.env with necessary configuration"
    fi
    
    print_info "Starting FastAPI backend on http://localhost:$BACKEND_PORT"
    
    # Activate virtual environment and start backend in background with APP_MODE env var
    source "$SCRIPT_DIR/../.venv/bin/activate"
    APP_MODE=customer nohup uvicorn main:app --reload --host 0.0.0.0 --port $BACKEND_PORT > "$BACKEND_DIR/backend-customer.log" 2>&1 &
    
    BACKEND_PID=$!
    echo $BACKEND_PID > "$BACKEND_DIR/.backend-customer.pid"
    
    # Wait a moment for the server to start
    sleep 2
    
    # Check if backend is running
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend started in CUSTOMER MODE (PID: $BACKEND_PID)"
        print_info "Backend logs: $BACKEND_DIR/backend-customer.log"
        print_success "Backend API: http://localhost:$BACKEND_PORT"
        print_success "API docs: http://localhost:$BACKEND_PORT/docs"
    else
        print_error "Backend failed to start. Check $BACKEND_DIR/backend-customer.log"
        exit 1
    fi
}

start_frontend() {
    print_header "Starting Frontend"
    
    cd "$FRONTEND_DIR"
    
    # Check if node_modules exists
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        print_info "node_modules not found. Running npm install..."
        npm install
    fi
    
    print_info "Starting Vite dev server on http://localhost:$FRONTEND_PORT"
    print_info "API URL: http://localhost:$BACKEND_PORT"
    
    # Start frontend in background with custom port and explicit API URL
    VITE_API_URL="http://localhost:$BACKEND_PORT" nohup npm run dev -- --port $FRONTEND_PORT > "$FRONTEND_DIR/frontend-customer.log" 2>&1 &
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$FRONTEND_DIR/.frontend-customer.pid"
    
    # Wait a moment for the server to start
    sleep 3
    
    # Check if frontend is running
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend started (PID: $FRONTEND_PID)"
        print_info "Frontend logs: $FRONTEND_DIR/frontend-customer.log"
        print_success "Frontend: http://localhost:$FRONTEND_PORT"
        print_info "API URL: http://localhost:$BACKEND_PORT"
        print_mode
    else
        print_error "Frontend failed to start. Check $FRONTEND_DIR/frontend-customer.log"
        exit 1
    fi
}

show_status() {
    print_header "Status (CUSTOMER MODE)"
    print_mode
    
    echo -e "\n${YELLOW}Backend:${NC}"
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_success "Running on http://localhost:$BACKEND_PORT"
        if [ -f "$BACKEND_DIR/.backend-customer.pid" ]; then
            PID=$(cat "$BACKEND_DIR/.backend-customer.pid")
            echo -e "  PID: $PID"
        fi
        echo -e "  ${CYAN}Mode: CUSTOMER${NC}"
    else
        print_error "Not running"
    fi
    
    echo -e "\n${YELLOW}Frontend:${NC}"
    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_success "Running on http://localhost:$FRONTEND_PORT"
        if [ -f "$FRONTEND_DIR/.frontend-customer.pid" ]; then
            PID=$(cat "$FRONTEND_DIR/.frontend-customer.pid")
            echo -e "  PID: $PID"
        fi
    else
        print_error "Not running"
    fi
    
    echo ""
}

show_logs() {
    local SERVICE=$1
    
    if [ "$SERVICE" = "backend" ]; then
        if [ -f "$BACKEND_DIR/backend-customer.log" ]; then
            tail -f "$BACKEND_DIR/backend-customer.log"
        else
            print_error "Backend log not found"
        fi
    elif [ "$SERVICE" = "frontend" ]; then
        if [ -f "$FRONTEND_DIR/frontend-customer.log" ]; then
            tail -f "$FRONTEND_DIR/frontend-customer.log"
        else
            print_error "Frontend log not found"
        fi
    else
        print_error "Invalid service. Use 'backend' or 'frontend'"
        exit 1
    fi
}

# Main script logic
COMMAND=${1:-all}

case $COMMAND in
    backend)
        stop_backend
        start_backend
        show_status
        ;;
    frontend)
        stop_frontend
        start_frontend
        show_status
        ;;
    all|restart)
        stop_backend
        stop_frontend
        start_backend
        start_frontend
        show_status
        ;;
    stop)
        stop_backend
        stop_frontend
        print_success "All services stopped"
        ;;
    status)
        show_status
        ;;
    logs)
        if [ -z "$2" ]; then
            print_error "Please specify service: backend or frontend"
            echo "Usage: ./dev-restart-customer.sh logs [backend|frontend]"
            exit 1
        fi
        show_logs "$2"
        ;;
    *)
        echo "Usage: $0 [backend|frontend|all|restart|stop|status|logs]"
        echo ""
        echo "🛡️  CUSTOMER MODE - Unbiased insights, no partner rankings"
        echo ""
        echo "Commands:"
        echo "  backend   - Restart only the backend (FastAPI)"
        echo "  frontend  - Restart only the frontend (Vite/React)"
        echo "  all       - Restart both backend and frontend (default)"
        echo "  restart   - Same as 'all'"
        echo "  stop      - Stop both services"
        echo "  status    - Show status of services"
        echo "  logs      - Show logs (requires: backend or frontend)"
        echo ""
        echo "Examples:"
        echo "  $0              # Restart everything in CUSTOMER mode"
        echo "  $0 backend      # Restart only backend in CUSTOMER mode"
        echo "  $0 status       # Check status"
        echo "  $0 logs backend # Tail backend logs"
        exit 1
        ;;
esac
