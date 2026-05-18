#!/usr/bin/env bash
# BarkMind Status Script

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$APP_DIR/runtime"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
BACKEND_PORT=8108
FRONTEND_PORT=3008

TS=$(date '+%Y-%m-%d %H:%M:%S')

echo ""
echo "  BarkMind Runtime Status — $TS"
echo "  ════════════════════════════════════════"

_check() {
    local name="$1"
    local pid_file="$2"
    local port="$3"

    local pid_line="  no PID file"
    local port_line
    local health_line=""

    if [[ -f "$pid_file" ]]; then
        PID=$(cat "$pid_file" 2>/dev/null || echo "")
        if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
            pid_line="  running  (PID $PID)"
        elif [[ -n "$PID" ]]; then
            pid_line="  STALE    (PID $PID — process gone)"
        fi
    fi

    # Use ss for reliable port detection (lsof -ti misses child process binds)
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        port_line="  :$port  IN USE"
    elif lsof -iTCP:"$port" -sTCP:LISTEN &>/dev/null 2>&1; then
        port_line="  :$port  IN USE"
    else
        port_line="  :$port  free"
    fi

    if [[ "$name" == "backend" ]]; then
        if HEALTH=$(curl -sf "http://127.0.0.1:$port/health" 2>/dev/null); then
            STATUS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','?'))" 2>/dev/null || echo "?")
            VERSION=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('version','?'))" 2>/dev/null || echo "?")
            health_line="  /health  OK (status=$STATUS version=$VERSION)"
        else
            health_line="  /health  NOT RESPONDING"
        fi
    fi

    echo ""
    echo "  $name"
    echo "    PID:    $pid_line"
    echo "    Port:  $port_line"
    [[ -n "$health_line" ]] && echo "    API:   $health_line"
}

_check "backend"  "$BACKEND_PID_FILE"  "$BACKEND_PORT"
_check "frontend" "$FRONTEND_PID_FILE" "$FRONTEND_PORT"

echo ""
echo "  Logs:"
echo "    backend:  tail -f $APP_DIR/logs/backend.log"
echo "    frontend: tail -f $APP_DIR/logs/frontend.log"
echo ""
echo "  Endpoints:"
echo "    API:   http://127.0.0.1:$BACKEND_PORT"
echo "    UI:    http://127.0.0.1:$FRONTEND_PORT"
echo "    Docs:  http://127.0.0.1:$BACKEND_PORT/docs"
echo "  ════════════════════════════════════════"
echo ""
