#!/usr/bin/env bash

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$APP_DIR/runtime"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
BACKEND_PORT=8107
FRONTEND_PORT=3007

echo "[BARKMIND] Status"
echo "────────────────────────────────────────────"

_check_process() {
    local name="$1"
    local pid_file="$2"
    local port="$3"

    local pid_status="no PID file"
    local port_status=""
    local health_status=""

    if [[ -f "$pid_file" ]]; then
        PID=$(cat "$pid_file")
        if kill -0 "$PID" 2>/dev/null; then
            pid_status="running (PID $PID)"
        else
            pid_status="stale PID file (PID $PID, process gone)"
        fi
    fi

    if lsof -ti:"$port" &>/dev/null; then
        port_status="port $port: IN USE"
    else
        port_status="port $port: free"
    fi

    if [[ "$name" == "backend" ]]; then
        if curl -sf "http://127.0.0.1:$port/health" &>/dev/null; then
            health_status="  /health: OK"
        else
            health_status="  /health: not responding"
        fi
    fi

    echo "  $name:"
    echo "    PID:    $pid_status"
    echo "    Port:   $port_status"
    [[ -n "$health_status" ]] && echo "   $health_status"
}

_check_process "backend" "$BACKEND_PID_FILE" "$BACKEND_PORT"
_check_process "frontend" "$FRONTEND_PID_FILE" "$FRONTEND_PORT"

echo ""
echo "  Logs:"
echo "    backend:  $APP_DIR/logs/backend.log"
echo "    frontend: $APP_DIR/logs/frontend.log"
echo "────────────────────────────────────────────"
