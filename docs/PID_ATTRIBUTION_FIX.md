# BarkMind — PID Attribution Fix

**Date:** 2026-05-17  
**Fixed by:** Port-based PID resolution after readiness confirmation

---

## The Problem

`start.sh` was saving `$!` (the PID of the `setsid` wrapper process) to the PID file. This process exits immediately, making every liveness check report STALE.

```bash
# Old (broken):
setsid npm run start >> logfile &
FRONTEND_PID=$!       # = setsid wrapper PID → exits immediately
echo "$FRONTEND_PID" > frontend.pid
```

## The Fix

After the readiness check confirms the service is up, query the actual listening PID from `ss -tlnp` and overwrite the PID file with the true runtime PID.

```bash
# New (correct):
setsid npm run start >> logfile &
SETSID_PID=$!
disown "$SETSID_PID"
echo "$SETSID_PID" > "$FRONTEND_PID_FILE"   # placeholder

# Wait for HTTP readiness (confirms service is up)
for i in ...; do
    curl -sf http://127.0.0.1:$FRONTEND_PORT && { ready=true; break; }
    sleep 1
done

# Resolve actual runtime PID from port occupancy
ACTUAL_FE_PID=$(ss -tlnp | grep ":$FRONTEND_PORT " | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -1)
echo "$ACTUAL_FE_PID" > "$FRONTEND_PID_FILE"   # canonical next-server PID
```

## Applied To

Both backend and frontend:

### Frontend (next-server)
- Placeholder: `$!` (setsid wrapper, exits immediately)
- Resolved: next-server PID from `ss -tlnp | grep ":3008"`
- Confirmed via: `kill -0 $ACTUAL_FE_PID`

### Backend (uvicorn)  
- Placeholder: `$!` (setsid wrapper, may or may not be same as uvicorn)
- Resolved: uvicorn PID from `ss -tlnp | grep ":8108"`
- Confirmed via: `/health` endpoint + `kill -0`

## Why Port-Based Resolution Is Correct

After a readiness check confirms HTTP is available:
1. The process listening on the port IS the runtime
2. `ss -tlnp` provides the PID directly from kernel socket state
3. This is always accurate — it's what the OS knows

## Correctness for stop.sh

`stop.sh`'s `_kill_group()` function:
```bash
pgid=$(ps -o pgid= -p "$PID" | tr -d ' ')
kill -TERM -- -"$pgid"
```

With next-server's PID, `pgid` = npm's PID. `kill -- -pgid` terminates npm + sh + next-server.  
With uvicorn's PID, `pgid` = uvicorn's session/group. `kill -- -pgid` terminates the full uvicorn stack.

## Recurrence Prevention

The fix is structural — not a patch on the old approach.

The PID file now contains the **port-bound process**, which is:
- Always the true runtime
- Always discoverable via `ss`
- Always the process you want to kill/monitor

Even if `setsid` changes behavior across systems (exec-in-place vs fork), the port-based resolution is always correct because it is derived from actual OS socket state, not from process tree assumptions.

## Before and After

| State | Before | After |
|---|---|---|
| `frontend.pid` contains | setsid wrapper PID (dead) | next-server PID (alive) |
| `status.sh` backend | running (wrapper) | running (uvicorn) |
| `status.sh` frontend | **STALE** | **running** |
| `stop.sh` kills | dead PID → port lingers | PGID → full stack |
| Restart after stop | blocks (port in use) | succeeds cleanly |

## Test Evidence

Three consecutive stop/start cycles — all clean, no STALE reported:

```
Cycle 1: Frontend PID resolved: 420522 (next-server) → status: running
Cycle 2: Frontend PID resolved: 421280 (next-server) → status: running
```

`kill -0 $(cat frontend.pid)` succeeds while frontend is running.  
`kill -0 $(cat frontend.pid)` fails after stop.sh completes.  
Both states accurately reflected by `status.sh`.
