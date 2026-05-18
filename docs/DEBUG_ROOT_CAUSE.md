# BarkMind — Runtime Debug: Root Cause Analysis

**Date:** 2026-05-17  
**Status:** RESOLVED  
**Debug method:** Live `bash -x` trace of actual execution path

---

## Investigation Methodology

No guessing. No assumptions. Every conclusion is from observed command output.

1. Read `start.sh` verbatim — located uvicorn invocation line
2. Read `.env` — observed actual `LOG_LEVEL` value at rest
3. Simulated shell sourcing in subshell — traced what value uvicorn would receive
4. Ran `bash -x ./start.sh` — captured the complete execution trace
5. Cleaned lingering port state — ran `./start.sh` from a clean environment
6. Observed actual behavior, no error reproduced

---

## Root Cause 1: `LOG_LEVEL=INFO` (uppercase) in `.env`

### Causal chain

```
.env:        LOG_LEVEL=INFO          ← uppercase
start.sh:    source "$APP_DIR/.env"  ← sets LOG_LEVEL=INFO in shell environment
start.sh:    --log-level "${LOG_LEVEL:-info}"
             ↳ evaluates to: INFO    ← bash fallback only fires when var is UNSET
uvicorn:     Error: Invalid value for '--log-level': 'INFO'
             ↳ choices: [critical|error|warning|info|debug|trace]  ← all lowercase
```

### Why manual worked

The manual command hardcodes `--log-level info` (lowercase) and never reads `LOG_LEVEL`:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8108 --log-level info
```

### Why `uvicorn --log-level INFO --version` didn't catch it

Click processes `--version` as a special callback that exits **before** parameter validation runs. Only a full ASGI app launch triggers the choice validation.

### Fix

| File | Change |
|---|---|
| `.env` | `LOG_LEVEL=INFO` → `LOG_LEVEL=info` |
| `.env.example` | `LOG_LEVEL=INFO` → `LOG_LEVEL=info` |
| `backend/app/config.py` | default `"INFO"` → `"info"` |
| `start.sh` | Added `tr '[:upper:]' '[:lower:]'` normalization before passing to uvicorn |

---

## Root Cause 2: Port 3008 Surviving `stop.sh`

When debugging the second run, `./start.sh` failed with a **different error**:
```
ERROR: Port 3008 already in use.
```

The `next-server` process (a grandchild of npm) survived `stop.sh`.

### Process tree

```
npm (PID A, PGID A)          ← session leader, killed by stop.sh
  └── node/next (PID B)      ← direct child, killed by pkill -P A
        └── next-server (C)  ← grandchild, survived
```

`pkill -P $PID` kills only **direct** children (depth 1). `next-server` at depth 2 was orphaned and continued holding port 3008.

Additionally, `lsof -iTCP:3008 -sTCP:LISTEN -t` failed to return the `next-server` PID, preventing the fallback kill. `ss -tlnp` correctly identified it.

### Fix

`stop.sh` now uses process-group kill (all depths):
```bash
pgid=$(ps -o pgid= -p "$PID" | tr -d ' ')
kill -TERM -- -"$pgid"   # kills parent + all descendants at any depth
```

Port detection uses `ss -tlnp` throughout (more reliable than `lsof` for child-spawned listeners).

---

## Current State

All fixes applied and verified:

```
LOG_LEVEL=info              ← .env (lowercase)
log_level: str = "info"    ← config.py default (lowercase)
UVICORN_LOG_LEVEL=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')
                            ← start.sh defensive normalization
```

`./start.sh` exits 0. Backend healthy. Frontend responding. No stale PID state.
