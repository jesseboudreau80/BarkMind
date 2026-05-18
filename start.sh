#!/usr/bin/env bash
# BarkMind Startup Script
# Ports: backend=8108, frontend=3008
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$APP_DIR/runtime"
LOG_DIR="$APP_DIR/logs"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
BACKEND_PORT=8108
FRONTEND_PORT=3008
START_TIME=$(date +%s)

_log()  { echo "[BARKMIND $(date '+%H:%M:%S')] $*"; }
_warn() { echo "[BARKMIND $(date '+%H:%M:%S')] WARN: $*"; }
_err()  { echo "[BARKMIND $(date '+%H:%M:%S')] ERROR: $*" >&2; }
_ok()   { echo "[BARKMIND $(date '+%H:%M:%S')] OK: $*"; }

_log "Starting BarkMind (backend=:$BACKEND_PORT frontend=:$FRONTEND_PORT)"

# ─── Ensure runtime/log dirs exist ──────────────────────────────────────────
mkdir -p "$RUNTIME_DIR" "$LOG_DIR"

# ─── Load .env ───────────────────────────────────────────────────────────────
if [[ -f "$APP_DIR/.env" ]]; then
    set -a; source "$APP_DIR/.env"; set +a
    _ok ".env loaded"
else
    _err ".env not found. Copy .env.example to .env and configure it."
    exit 1
fi

# ─── Dependency Validation ───────────────────────────────────────────────────
_log "Validating dependencies..."

MISSING_DEPS=()

if ! command -v python3 &>/dev/null; then
    MISSING_DEPS+=("python3")
fi

if ! command -v uvicorn &>/dev/null; then
    MISSING_DEPS+=("uvicorn (pip install -r $BACKEND_DIR/requirements.txt)")
fi

if ! command -v psql &>/dev/null; then
    _warn "psql not found — cannot verify database. Proceeding."
fi

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    _err "Missing required dependencies:"
    for dep in "${MISSING_DEPS[@]}"; do
        _err "  - $dep"
    done
    exit 1
fi

_ok "All required dependencies found"

# ─── Backend file check ───────────────────────────────────────────────────────
if [[ ! -f "$BACKEND_DIR/app/main.py" ]]; then
    _err "Backend not found at $BACKEND_DIR/app/main.py"
    exit 1
fi

# ─── Port Conflict Enforcement ────────────────────────────────────────────────
_port_in_use() {
    ss -tlnp 2>/dev/null | grep -q ":$1 " || lsof -iTCP:"$1" -sTCP:LISTEN &>/dev/null 2>&1
}

if _port_in_use "$BACKEND_PORT"; then
    _err "Port $BACKEND_PORT already in use. Run stop.sh first, or check:"
    _err "  ss -tlnp | grep $BACKEND_PORT"
    exit 1
fi

if _port_in_use "$FRONTEND_PORT"; then
    _err "Port $FRONTEND_PORT already in use. Run stop.sh first, or check:"
    _err "  lsof -i:$FRONTEND_PORT"
    exit 1
fi

_ok "Ports $BACKEND_PORT and $FRONTEND_PORT are free"

# ─── Stale PID Cleanup ───────────────────────────────────────────────────────
for PID_FILE in "$BACKEND_PID_FILE" "$FRONTEND_PID_FILE"; do
    if [[ -f "$PID_FILE" ]]; then
        OLD_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
            _err "Process $OLD_PID from $(basename $PID_FILE) is still running. Run stop.sh first."
            exit 1
        fi
        rm -f "$PID_FILE"
        _warn "Removed stale PID file: $(basename $PID_FILE)"
    fi
done

# ─── Media Root ───────────────────────────────────────────────────────────────
MEDIA_ROOT="${MEDIA_ROOT:-$APP_DIR/media}"
if [[ ! -d "$MEDIA_ROOT" ]]; then
    mkdir -p "$MEDIA_ROOT/cases"
    _ok "Created media root: $MEDIA_ROOT"
fi
if [[ ! -w "$MEDIA_ROOT" ]]; then
    _err "MEDIA_ROOT ($MEDIA_ROOT) is not writable."
    exit 1
fi

# ─── Database Connectivity Check ─────────────────────────────────────────────
_log "Checking database connectivity..."
DB_URL="${DATABASE_URL:-}"
if [[ -n "$DB_URL" ]] && command -v python3 &>/dev/null; then
    DB_OK=$(python3 -c "
import asyncio, sys
async def check():
    try:
        import asyncpg
        url = '$DB_URL'.replace('postgresql+asyncpg://', 'postgresql://')
        conn = await asyncpg.connect(url, timeout=5)
        await conn.close()
        print('ok')
    except Exception as e:
        print(f'error: {e}')
asyncio.run(check())
" 2>/dev/null)
    if [[ "$DB_OK" == "ok" ]]; then
        _ok "Database connection verified"
    else
        _warn "Database check: $DB_OK — backend may fail to start"
    fi
fi

# ─── Run Pending Migrations ───────────────────────────────────────────────────
_log "Checking migrations..."
if command -v alembic &>/dev/null && [[ -f "$BACKEND_DIR/alembic.ini" ]]; then
    MIGRATION_RESULT=$(cd "$BACKEND_DIR" && alembic current 2>&1 | tail -1)
    _ok "Alembic current: $MIGRATION_RESULT"
    # Auto-apply pending migrations
    cd "$BACKEND_DIR" && alembic upgrade head --quiet 2>/dev/null && _ok "Migrations up to date" || _warn "Migration check failed — may already be current"
    cd "$APP_DIR"
fi

# ─── Start Backend ────────────────────────────────────────────────────────────
# Uvicorn requires lowercase log level. Normalize defensively regardless of .env case.
UVICORN_LOG_LEVEL=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')
_log "Starting backend (uvicorn on :$BACKEND_PORT, log-level=$UVICORN_LOG_LEVEL)..."
cd "$BACKEND_DIR"
setsid uvicorn app.main:app \
    --host 127.0.0.1 \
    --port "$BACKEND_PORT" \
    --log-level "$UVICORN_LOG_LEVEL" \
    >> "$LOG_DIR/backend.log" 2>&1 &
SETSID_BACKEND_PID=$!
disown "$SETSID_BACKEND_PID"
echo "$SETSID_BACKEND_PID" > "$BACKEND_PID_FILE"  # placeholder — overwritten after health check
cd "$APP_DIR"
_log "Backend launch initiated (setsid wrapper PID $SETSID_BACKEND_PID, resolving actual runtime...)"

# ─── Backend Health Check ─────────────────────────────────────────────────────
_log "Waiting for backend health..."
MAX_WAIT=30
BACKEND_READY=false
for i in $(seq 1 $MAX_WAIT); do
    if curl -sf "http://127.0.0.1:$BACKEND_PORT/health" &>/dev/null; then
        BACKEND_READY=true
        _ok "Backend healthy after ${i}s"
        break
    fi
    # Check both the setsid wrapper and the actual port occupant
    if ! kill -0 "$SETSID_BACKEND_PID" 2>/dev/null && \
       ! ss -tlnp 2>/dev/null | grep -q ":$BACKEND_PORT "; then
        _err "Backend process died before becoming healthy. Check logs: tail -50 $LOG_DIR/backend.log"
        exit 1
    fi
    sleep 1
done

if [[ "$BACKEND_READY" == "false" ]]; then
    _warn "Backend did not respond within ${MAX_WAIT}s. Check logs:"
    _warn "  tail -50 $LOG_DIR/backend.log"
fi

# ── PID attribution fix ───────────────────────────────────────────────────────
# Resolve the actual uvicorn PID from port occupancy — not the setsid wrapper.
ACTUAL_BACKEND_PID=$(ss -tlnp 2>/dev/null \
    | grep ":$BACKEND_PORT " \
    | sed -n 's/.*pid=\([0-9]*\).*/\1/p' \
    | head -1)

if [[ -n "$ACTUAL_BACKEND_PID" ]] && kill -0 "$ACTUAL_BACKEND_PID" 2>/dev/null; then
    echo "$ACTUAL_BACKEND_PID" > "$BACKEND_PID_FILE"
    _ok "Backend runtime PID resolved: $ACTUAL_BACKEND_PID (uvicorn on :$BACKEND_PORT)"
else
    _warn "Could not resolve backend runtime PID — using setsid wrapper PID $SETSID_BACKEND_PID"
fi

# ─── Start Frontend ───────────────────────────────────────────────────────────
if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
    _warn "Frontend not initialized (package.json missing). Skipping."
elif [[ ! -d "$FRONTEND_DIR/.next" ]]; then
    _warn "Frontend not built. Run: cd $FRONTEND_DIR && npm run build"
    _warn "Skipping frontend startup."
else
    _log "Starting frontend (Next.js on :$FRONTEND_PORT)..."
    cd "$FRONTEND_DIR"
    setsid npm run start \
        >> "$LOG_DIR/frontend.log" 2>&1 &
    # NOTE: setsid forks when the calling process is already a session leader.
    # $! captures the setsid wrapper PID which exits immediately after forking.
    # The actual npm process gets a NEW PID that we cannot know until it appears.
    # We use a placeholder PID here and overwrite it after the runtime is confirmed.
    SETSID_PID=$!
    disown "$SETSID_PID"
    echo "$SETSID_PID" > "$FRONTEND_PID_FILE"  # placeholder — overwritten below
    cd "$APP_DIR"
    _log "Frontend launch initiated (setsid wrapper PID $SETSID_PID, resolving actual runtime...)"

    # Frontend readiness check — wait for HTTP response on :$FRONTEND_PORT
    MAX_FE_WAIT=20
    FE_READY=false
    for i in $(seq 1 $MAX_FE_WAIT); do
        if curl -sf "http://127.0.0.1:$FRONTEND_PORT" -o /dev/null &>/dev/null; then
            FE_READY=true
            _ok "Frontend HTTP ready after ${i}s"
            break
        fi
        if [[ $i -eq $MAX_FE_WAIT ]]; then
            _warn "Frontend did not respond within ${MAX_FE_WAIT}s (may still be starting)"
        fi
        sleep 1
    done

    # ── PID attribution fix ───────────────────────────────────────────────────
    # Now that the frontend is confirmed ready, resolve the actual runtime PID.
    # The process listening on :$FRONTEND_PORT is next-server — the canonical
    # long-lived runtime. Its PGID == npm's PID, so kill(-PGID) terminates all.
    ACTUAL_FE_PID=$(ss -tlnp 2>/dev/null \
        | grep ":$FRONTEND_PORT " \
        | sed -n 's/.*pid=\([0-9]*\).*/\1/p' \
        | head -1)

    if [[ -n "$ACTUAL_FE_PID" ]] && kill -0 "$ACTUAL_FE_PID" 2>/dev/null; then
        echo "$ACTUAL_FE_PID" > "$FRONTEND_PID_FILE"
        _ok "Frontend runtime PID resolved: $ACTUAL_FE_PID (next-server on :$FRONTEND_PORT)"
    else
        _warn "Could not resolve frontend runtime PID — status.sh may show stale"
    fi
fi

# ─── Aegis Registration ───────────────────────────────────────────────────────
AEGIS_URL="${AEGIS_BASE_URL:-http://127.0.0.1:8102}"
AEGIS_EMAIL="${AEGIS_USER_EMAIL:-admin@dpvet.com}"

_log "Registering with Aegis at $AEGIS_URL..."
AEGIS_PAYLOAD="{\"app_id\":\"barkmind\",\"name\":\"BarkMind\",\"backend_port\":$BACKEND_PORT,\"frontend_port\":$FRONTEND_PORT,\"backend_url\":\"http://127.0.0.1:$BACKEND_PORT\",\"frontend_url\":\"http://127.0.0.1:$FRONTEND_PORT\",\"health_endpoint\":\"http://127.0.0.1:$BACKEND_PORT/health\",\"meta_endpoint\":\"http://127.0.0.1:$BACKEND_PORT/.well-known/aegis-meta\",\"lifecycle\":[\"start\",\"stop\",\"restart\",\"status\"]}"

HTTP_STATUS=$(curl -sf -o /dev/null -w "%{http_code}" -X POST "$AEGIS_URL/api/apps/register" \
    -H "Content-Type: application/json" \
    -H "X-User-Email: $AEGIS_EMAIL" \
    -d "$AEGIS_PAYLOAD" 2>/dev/null || echo "000")

case "$HTTP_STATUS" in
    200|201|204) _ok "Aegis registration successful (HTTP $HTTP_STATUS)" ;;
    000)         _warn "Aegis unavailable — running without topology registration" ;;
    *)           _warn "Aegis registration returned HTTP $HTTP_STATUS — continuing" ;;
esac

# ─── Startup Summary ─────────────────────────────────────────────────────────
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "[BARKMIND] ════════════════════════════════════════"
echo "[BARKMIND]   BarkMind is running  (${ELAPSED}s startup)"
echo "[BARKMIND]   Backend:  http://127.0.0.1:$BACKEND_PORT"
echo "[BARKMIND]   Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "[BARKMIND]   API docs: http://127.0.0.1:$BACKEND_PORT/docs"
echo "[BARKMIND]   Health:   http://127.0.0.1:$BACKEND_PORT/health"
echo "[BARKMIND]   Logs:     $LOG_DIR/"
echo "[BARKMIND] ════════════════════════════════════════"
