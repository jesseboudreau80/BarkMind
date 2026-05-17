#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$APP_DIR/runtime"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"

echo "[BARKMIND] Stopping BarkMind..."

_stop_process() {
    local name="$1"
    local pid_file="$2"

    if [[ -f "$pid_file" ]]; then
        PID=$(cat "$pid_file")
        if kill -0 "$PID" 2>/dev/null; then
            echo "[BARKMIND] Stopping $name (PID $PID)..."
            kill -TERM "$PID" 2>/dev/null || true
            for i in $(seq 1 10); do
                if ! kill -0 "$PID" 2>/dev/null; then
                    echo "[BARKMIND] $name stopped."
                    break
                fi
                if [[ $i -eq 10 ]]; then
                    echo "[BARKMIND] $name did not stop gracefully. Sending SIGKILL."
                    kill -KILL "$PID" 2>/dev/null || true
                fi
                sleep 1
            done
        else
            echo "[BARKMIND] $name PID $PID not running (stale PID file)."
        fi
        rm -f "$pid_file"
    else
        echo "[BARKMIND] No $name PID file found."
    fi
}

_stop_process "backend" "$BACKEND_PID_FILE"
_stop_process "frontend" "$FRONTEND_PID_FILE"

echo "[BARKMIND] Stopped."
