#!/usr/bin/env bash
# BarkMind Stop Script
# Kills the full process group (parent + all descendants) to ensure port release.
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

# Get the PID holding a port (using ss which is more reliable than lsof for child procs)
_pid_on_port() {
    local port="$1"
    ss -tlnp 2>/dev/null | grep ":$port " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -1 || echo ""
}

# Check if a port is occupied
_port_in_use() {
    ss -tlnp 2>/dev/null | grep -q ":$1 "
}

# Kill a process AND its entire process group (handles grandchildren like next-server)
_kill_group() {
    local pid="$1"
    local sig="${2:-TERM}"
    if [[ -z "$pid" ]] || ! kill -0 "$pid" 2>/dev/null; then
        return
    fi
    # Get the process group ID — for setsid processes, PGID = session leader PID
    local pgid
    pgid=$(ps -o pgid= -p "$pid" 2>/dev/null | tr -d ' ' || echo "$pid")
    # Kill the entire process group (covers parent + all children at all depths)
    if [[ -n "$pgid" ]]; then
        kill -"$sig" -- -"$pgid" 2>/dev/null || true
    fi
    # Also kill the PID directly as fallback
    kill -"$sig" "$pid" 2>/dev/null || true
}

_stop_process() {
    local name="$1"
    local pid_file="$2"
    local port="$3"

    if [[ -f "$pid_file" ]]; then
        PID=$(cat "$pid_file" 2>/dev/null || echo "")
        rm -f "$pid_file"

        if [[ -z "$PID" ]]; then
            # No PID — try by port
            if _port_in_use "$port"; then
                local stray
                stray=$(_pid_on_port "$port")
                if [[ -n "$stray" ]]; then
                    _log "$name: killing stray port-$port process (PID $stray)"
                    _kill_group "$stray" TERM
                fi
            fi
            return
        fi

        if kill -0 "$PID" 2>/dev/null; then
            _log "Stopping $name (PID $PID, full process group)..."
            _kill_group "$PID" TERM
        else
            _log "$name PID $PID not running (stale PID file)"
        fi
    fi

    # Wait for port release — covers the case where process tree outlives the PID
    local freed=false
    for i in $(seq 1 12); do
        if ! _port_in_use "$port"; then
            freed=true
            break
        fi
        if [[ $i -eq 8 ]]; then
            # Escalate to SIGKILL for anything still holding the port
            local stray
            stray=$(_pid_on_port "$port")
            if [[ -n "$stray" ]]; then
                _log "$name: SIGKILL for port-$port straggler (PID $stray)"
                _kill_group "$stray" KILL
            fi
        fi
        sleep 1
    done

    if [[ "$freed" == "true" ]]; then
        _ok "$name stopped"
    else
        _log "WARNING: $name port $port may still be in use"
    fi
}

_stop_process "backend"  "$BACKEND_PID_FILE"  "$BACKEND_PORT"
_stop_process "frontend" "$FRONTEND_PID_FILE" "$FRONTEND_PORT"

_ok "BarkMind stopped"
