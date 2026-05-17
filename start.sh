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
if lsof -ti:$BACKEND_PORT &>/dev/null; then
    _err "Port $BACKEND_PORT already in use. Run stop.sh first, or check:"
    _err "  lsof -i:$BACKEND_PORT"
    exit 1
fi

if lsof -ti:$FRONTEND_PORT &>/dev/null; then
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
_log "Starting backend (uvicorn on :$BACKEND_PORT)..."
cd "$BACKEND_DIR"
setsid uvicorn app.main:app \
    --host 127.0.0.1 \
    --port "$BACKEND_PORT" \
    --log-level "${LOG_LEVEL:-info}" \
    >> "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
disown "$BACKEND_PID"
echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
cd "$APP_DIR"
_ok "Backend process started (PID $BACKEND_PID)"

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
    # Check if process died
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        _err "Backend process $BACKEND_PID died. Check logs: tail -50 $LOG_DIR/backend.log"
        exit 1
    fi
    sleep 1
done

if [[ "$BACKEND_READY" == "false" ]]; then
    _warn "Backend did not respond within ${MAX_WAIT}s. Check logs:"
    _warn "  tail -50 $LOG_DIR/backend.log"
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
    FRONTEND_PID=$!
    disown "$FRONTEND_PID"
    echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
    cd "$APP_DIR"
    _ok "Frontend process started (PID $FRONTEND_PID)"

    # Frontend readiness check
    MAX_FE_WAIT=20
    for i in $(seq 1 $MAX_FE_WAIT); do
        if curl -sf "http://127.0.0.1:$FRONTEND_PORT" -o /dev/null &>/dev/null; then
            _ok "Frontend ready after ${i}s"
            break
        fi
        if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            _warn "Frontend process died. Check logs: tail -50 $LOG_DIR/frontend.log"
            break
        fi
        if [[ $i -eq $MAX_FE_WAIT ]]; then
            _warn "Frontend did not respond within ${MAX_FE_WAIT}s (may still be starting)"
        fi
        sleep 1
    done
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
