# BarkMind — Runtime Fix Report

**Date:** 2026-05-17  
**Status:** ALL ISSUES RESOLVED AND VERIFIED

---

## Summary

Two root causes were found and fixed:

1. **`LOG_LEVEL=INFO` (uppercase)** in `.env` → passed to uvicorn as `--log-level INFO` → uvicorn rejects uppercase
2. **`next-server` grandchild surviving `stop.sh`** → port 3008 not released → restart blocked

---

## Fix 1: Log Level Case Normalization

### What was broken

`.env` contained `LOG_LEVEL=INFO` (uppercase Python convention). `start.sh` passed it directly to uvicorn via `"${LOG_LEVEL:-info}"`. Uvicorn validates `--log-level` choices as lowercase-only.

The bash expression `"${LOG_LEVEL:-info}"`:
- Substitutes `info` only when `LOG_LEVEL` is **unset or empty**
- When `LOG_LEVEL=INFO` is set, it passes `INFO` literally
- The fallback `:-info` is never activated

### Files changed

**`.env`**
```diff
-LOG_LEVEL=INFO
+LOG_LEVEL=info
```

**`.env.example`**
```diff
-LOG_LEVEL=INFO
+LOG_LEVEL=info
```

**`backend/app/config.py`**
```diff
-    log_level: str = "INFO"
+    log_level: str = "info"
```
(Python's `logging.getattr(level.upper())` handles both cases — Python never had this problem. Only uvicorn's CLI is case-sensitive.)

**`start.sh`** — defensive normalization added before uvicorn invocation:
```bash
# Before:
--log-level "${LOG_LEVEL:-info}"

# After:
UVICORN_LOG_LEVEL=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')
--log-level "$UVICORN_LOG_LEVEL"
```

The `tr` normalization is belt-and-suspenders: even if a future operator sets `LOG_LEVEL=DEBUG` or `LOG_LEVEL=WARNING` (uppercase) in their `.env`, it will be safely lowercased before uvicorn receives it.

---

## Fix 2: Process Group Kill for Clean Port Release

### What was broken

`stop.sh` killed the npm PID and its direct children (`pkill -P $PID`), but `next-server` — a **grandchild** of npm — survived and continued holding port 3008.

Additionally, `lsof -iTCP:3008 -sTCP:LISTEN -t` failed to detect `next-server`, so the fallback kill never fired.

### Files changed

**`stop.sh`** — `_kill_group()` function:
```bash
# Before: shallow kill (depth 1 only)
pkill -TERM -P "$PID"
kill -TERM "$PID"

# After: full process group kill (all depths)
pgid=$(ps -o pgid= -p "$PID" | tr -d ' ')
kill -TERM -- -"$pgid"   # kills every process in the group
kill -TERM "$PID"        # direct kill as fallback
```

For `setsid` processes, `PGID == PID of session leader`. All descendants inherit this PGID. Killing `-$PGID` terminates the entire process tree at once.

**`stop.sh`** — port detection via `ss`:
```bash
# Before (unreliable):
lsof -iTCP:"$port" -sTCP:LISTEN -t

# After (reliable):
ss -tlnp | grep ":$port " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -1
```

**`status.sh`** and **`start.sh`** — port conflict check:
```bash
# Before:
lsof -ti:"$port" &>/dev/null

# After:
ss -tlnp | grep -q ":$port " || lsof -iTCP:"$port" -sTCP:LISTEN &>/dev/null
```

---

## Recurrence Prevention

### Log level

Any value in `.env` (uppercase, lowercase, mixed) is safely normalized by `tr` in `start.sh` before reaching uvicorn. The default in `.env.example` and `config.py` is now lowercase to set the correct expectation.

### Port release

The process group kill approach handles any process tree depth. `ss -tlnp` is used throughout for reliable port occupancy detection, as it identifies listener PIDs regardless of process parent/child relationships.

---

## Verified Tests

| Test | Result |
|---|---|
| `./start.sh` exits 0 | PASS |
| Backend alive after start | PASS (PID 389109) |
| `/health` responds `{"status":"ok"}` | PASS |
| `./status.sh` backend `:8108 IN USE` | PASS |
| `./status.sh` frontend `:3008 IN USE` | PASS |
| `./stop.sh` releases both ports | PASS |
| `./restart.sh` completes without port conflict | PASS |
| No uppercase `INFO` in runtime path | PASS (grep clean) |
| No stale PID state | PASS |
| PID files correctly written | PASS |
| Migration check passes | PASS (b698e6352af2, head) |
| Aegis Lite on :8107 unaffected | PASS |
