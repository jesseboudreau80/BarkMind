#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$APP_DIR/runtime"
LOG_DIR="$APP_DIR/logs"
BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"
BACKEND_PORT=8107
FRONTEND_PORT=3007

echo "[BARKMIND] Starting BarkMind..."
echo "[BARKMIND] Backend port: $BACKEND_PORT | Frontend port: $FRONTEND_PORT"

# ─── Load .env ────────────────────────────────────────────────────────────────
if [[ -f "$APP_DIR/.env" ]]; then
    set -a
    source "$APP_DIR/.env"
    set +a
else
    echo "[BARKMIND] ERROR: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# ─── Port Conflict Enforcement ────────────────────────────────────────────────
if lsof -ti:$BACKEND_PORT &>/dev/null; then
    echo "[BARKMIND] ERROR: Port $BACKEND_PORT is already in use. Refusing to start."
    echo "[BARKMIND]        Run: lsof -i:$BACKEND_PORT to identify the occupant."
    exit 1
fi

if lsof -ti:$FRONTEND_PORT &>/dev/null; then
    echo "[BARKMIND] ERROR: Port $FRONTEND_PORT is already in use. Refusing to start."
    echo "[BARKMIND]        Run: lsof -i:$FRONTEND_PORT to identify the occupant."
    exit 1
fi

# ─── PID Conflict Check ───────────────────────────────────────────────────────
if [[ -f "$BACKEND_PID_FILE" ]]; then
    EXISTING_PID=$(cat "$BACKEND_PID_FILE")
    if kill -0 "$EXISTING_PID" 2>/dev/null; then
        echo "[BARKMIND] ERROR: Backend already running (PID $EXISTING_PID). Run stop.sh first."
        exit 1
    fi
    rm -f "$BACKEND_PID_FILE"
fi

if [[ -f "$FRONTEND_PID_FILE" ]]; then
    EXISTING_PID=$(cat "$FRONTEND_PID_FILE")
    if kill -0 "$EXISTING_PID" 2>/dev/null; then
        echo "[BARKMIND] ERROR: Frontend already running (PID $EXISTING_PID). Run stop.sh first."
        exit 1
    fi
    rm -f "$FRONTEND_PID_FILE"
fi

# ─── Media Root Check ────────────────────────────────────────────────────────
MEDIA_ROOT="${MEDIA_ROOT:-$APP_DIR/media}"
if [[ ! -d "$MEDIA_ROOT" ]]; then
    echo "[BARKMIND] Creating media root: $MEDIA_ROOT"
    mkdir -p "$MEDIA_ROOT/cases"
fi
if [[ ! -w "$MEDIA_ROOT" ]]; then
    echo "[BARKMIND] ERROR: MEDIA_ROOT ($MEDIA_ROOT) is not writable."
    exit 1
fi

# ─── Backend (FastAPI via uvicorn) ───────────────────────────────────────────
BACKEND_DIR="$APP_DIR/backend"

if [[ ! -f "$BACKEND_DIR/app/main.py" ]]; then
    echo "[BARKMIND] ERROR: Backend not yet implemented ($BACKEND_DIR/app/main.py not found)."
    echo "[BARKMIND]        Run Phase 1 build first."
    exit 1
fi

if ! command -v uvicorn &>/dev/null; then
    echo "[BARKMIND] ERROR: uvicorn not found. Install backend dependencies first:"
    echo "[BARKMIND]        pip install -r $BACKEND_DIR/requirements.txt"
    exit 1
fi

echo "[BARKMIND] Starting backend..."
cd "$BACKEND_DIR"
setsid uvicorn app.main:app \
    --host 127.0.0.1 \
    --port "$BACKEND_PORT" \
    --log-level "${LOG_LEVEL:-info}" \
    >> "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
disown "$BACKEND_PID"
echo "$BACKEND_PID" > "$BACKEND_PID_FILE"
echo "[BARKMIND] Backend started (PID $BACKEND_PID)"
cd "$APP_DIR"

# ─── Frontend (Next.js) ──────────────────────────────────────────────────────
FRONTEND_DIR="$APP_DIR/frontend"

if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
    echo "[BARKMIND] WARNING: Frontend not yet implemented ($FRONTEND_DIR/package.json not found)."
    echo "[BARKMIND]          Skipping frontend startup."
else
    if [[ ! -d "$FRONTEND_DIR/.next" ]]; then
        echo "[BARKMIND] WARNING: Frontend not built. Run: cd $FRONTEND_DIR && npm run build"
        echo "[BARKMIND]          Skipping frontend startup."
    else
        echo "[BARKMIND] Starting frontend..."
        cd "$FRONTEND_DIR"
        setsid npm run start \
            >> "$LOG_DIR/frontend.log" 2>&1 &
        FRONTEND_PID=$!
        disown "$FRONTEND_PID"
        echo "$FRONTEND_PID" > "$FRONTEND_PID_FILE"
        echo "[BARKMIND] Frontend started (PID $FRONTEND_PID)"
        cd "$APP_DIR"
    fi
fi

# ─── Wait for backend health ──────────────────────────────────────────────────
echo "[BARKMIND] Waiting for backend to become healthy..."
MAX_WAIT=20
for i in $(seq 1 $MAX_WAIT); do
    if curl -sf "http://127.0.0.1:$BACKEND_PORT/health" &>/dev/null; then
        echo "[BARKMIND] Backend is healthy."
        break
    fi
    if [[ $i -eq $MAX_WAIT ]]; then
        echo "[BARKMIND] WARNING: Backend did not respond to /health within ${MAX_WAIT}s."
        echo "[BARKMIND]          Check logs: tail -f $LOG_DIR/backend.log"
    fi
    sleep 1
done

# ─── Aegis Registration ───────────────────────────────────────────────────────
AEGIS_URL="${AEGIS_BASE_URL:-http://127.0.0.1:8102}"
AEGIS_EMAIL="${AEGIS_USER_EMAIL:-admin@dpvet.com}"

echo "[BARKMIND] Attempting Aegis registration..."
AEGIS_PAYLOAD=$(cat <<EOF
{
  "app_id": "barkmind",
  "name": "BarkMind",
  "backend_port": $BACKEND_PORT,
  "frontend_port": $FRONTEND_PORT,
  "backend_url": "http://127.0.0.1:$BACKEND_PORT",
  "frontend_url": "http://127.0.0.1:$FRONTEND_PORT",
  "health_endpoint": "http://127.0.0.1:$BACKEND_PORT/health",
  "meta_endpoint": "http://127.0.0.1:$BACKEND_PORT/.well-known/aegis-meta",
  "lifecycle": ["start", "stop", "restart", "status"]
}
EOF
)

AEGIS_RESPONSE=$(curl -sf -X POST "$AEGIS_URL/api/apps/register" \
    -H "Content-Type: application/json" \
    -H "X-User-Email: $AEGIS_EMAIL" \
    -d "$AEGIS_PAYLOAD" 2>&1) || true

if [[ -z "$AEGIS_RESPONSE" ]]; then
    echo "[BARKMIND] WARNING: Aegis registration failed or Aegis unavailable. Continuing anyway."
    echo "[BARKMIND]          BarkMind is running but not topology-registered."
else
    echo "[BARKMIND] Aegis registration: $AEGIS_RESPONSE"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "[BARKMIND] ─────────────────────────────────────────"
echo "[BARKMIND]   BarkMind is running"
echo "[BARKMIND]   Backend:  http://127.0.0.1:$BACKEND_PORT"
echo "[BARKMIND]   Frontend: http://127.0.0.1:$FRONTEND_PORT"
echo "[BARKMIND]   Logs:     $LOG_DIR/"
echo "[BARKMIND] ─────────────────────────────────────────"
