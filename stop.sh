#!/usr/bin/env bash
# BarkMind Stop Script
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$APP_DIR/runtime"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
BACKEND_PORT=8108
FRONTEND_PORT=3008

_log() { echo "[BARKMIND $(date '+%H:%M:%S')] $*"; }
_ok()  { echo "[BARKMIND $(date '+%H:%M:%S')] OK: $*"; }

_log "Stopping BarkMind..."

_stop_process() {
    local name="$1"
    local pid_file="$2"
    local port="$3"

    if [[ -f "$pid_file" ]]; then
        PID=$(cat "$pid_file" 2>/dev/null || echo "")
        if [[ -z "$PID" ]]; then
            rm -f "$pid_file"
            return
        fi

        if kill -0 "$PID" 2>/dev/null; then
            _log "Stopping $name (PID $PID)..."
            kill -TERM "$PID" 2>/dev/null || true

            # Wait for graceful shutdown
            for i in $(seq 1 10); do
                if ! kill -0 "$PID" 2>/dev/null; then
                    _ok "$name stopped gracefully"
                    break
                fi
                if [[ $i -eq 10 ]]; then
                    _log "$name did not stop gracefully — sending SIGKILL"
                    kill -KILL "$PID" 2>/dev/null || true
                fi
                sleep 1
            done
        else
            _log "$name PID $PID not running (stale PID file)"
        fi
        rm -f "$pid_file"
    else
        # Fallback: kill by port occupancy
        local LEFTOVER_PID
        LEFTOVER_PID=$(lsof -ti:"$port" 2>/dev/null || echo "")
        if [[ -n "$LEFTOVER_PID" ]]; then
            _log "$name: killing port-$port process (PID $LEFTOVER_PID)"
            kill -TERM "$LEFTOVER_PID" 2>/dev/null || true
            sleep 2
            kill -KILL "$LEFTOVER_PID" 2>/dev/null || true
        else
            _log "$name: not running"
        fi
    fi
}

_stop_process "backend"  "$BACKEND_PID_FILE"  "$BACKEND_PORT"
_stop_process "frontend" "$FRONTEND_PID_FILE" "$FRONTEND_PORT"

_ok "BarkMind stopped"
