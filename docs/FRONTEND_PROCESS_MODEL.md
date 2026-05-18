# BarkMind — Frontend Process Model

**Date:** 2026-05-17

---

## Process Tree (Post-Start)

```
PID 1 (init)
  └── npm run start (PID B, PPID=1, PGID=B, SID=B)    ← session leader
        └── sh -c "next start -p 3008" (PID C)
              └── next-server (PID D)                   ← canonical runtime
                    ├── holds port :3008
                    └── serves HTTP (307 redirect → /cases)
```

### Why PPID=1 for npm

`setsid` creates a new session. When called from a session leader (bash):
1. `setsid` forks → child (new PID B) calls `setsid()` → new session (SID=B)
2. Parent (`setsid` wrapper = `$!`) exits immediately
3. Child execs npm
4. npm's PPID becomes 1 (init) after the parent exits

### PID Relationships

| Process | Role | Lifecycle |
|---|---|---|
| `setsid` wrapper (`$!`) | Fork launcher | Exits immediately after fork |
| npm (PID B) | Script runner | Alive while next-server runs |
| sh (PID C) | Shell wrapper for `next start` | Alive while next-server runs |
| next-server (PID D) | **Canonical runtime** | Long-lived, holds :3008 |

### Process Group (PGID = npm's PID B)

All processes share PGID = B (npm's PID). This means:
```bash
kill -TERM -- -B    # kills npm + sh + next-server in one signal
```

---

## Canonical Runtime PID

**next-server (PID D)** is the canonical runtime because:
1. It is the process holding :3008 (confirmed by `ss -tlnp`)
2. It is long-lived (outlives npm and sh)
3. Its PGID = npm's PID → `kill -TERM -- -PGID` terminates the entire stack
4. `kill -0 D` accurately reflects whether the frontend is serving

`status.sh` performs `kill -0 $PID` to check liveness. With D in the PID file, this check is always accurate.

---

## Why the Original Approach Failed

`start.sh` saved `$!` (the setsid wrapper) to `frontend.pid`. The setsid wrapper exits immediately, so:
- `kill -0 $!` fails immediately → STALE
- But next-server is alive and serving on :3008

**The lie:** PID file says dead. Reality says alive.

---

## Fixed PID Attribution

`start.sh` now:
1. Starts `setsid npm run start &` as before
2. Waits for HTTP readiness on :3008
3. Queries `ss -tlnp | grep ":3008"` → gets next-server's actual PID
4. Overwrites `frontend.pid` with next-server's PID

Result: PID file always reflects the actual serving process.

---

## Stop Behavior

`stop.sh` reads `frontend.pid` (now = next-server PID D), then:
1. Gets PGID of D: `ps -o pgid= -p D` = B (npm's PID)
2. Sends `kill -TERM -- -B`: kills npm + sh + next-server in one shot
3. Verifies :3008 is free via `ss -tlnp`

---

## Backend Process Model (For Reference)

`setsid uvicorn ... &` results in a slightly different tree:

```
setsid wrapper ($!, PPID=bash)   ← may stay alive briefly as parent of uvicorn
  └── uvicorn (PID A+1)          ← actual runtime, holds :8108
```

The setsid wrapper for uvicorn may linger longer than for npm. Same resolution applied: after the health check, `backend.pid` is overwritten with the actual uvicorn PID from `ss -tlnp`.

---

## Invariants Guaranteed After Fix

1. `runtime/frontend.pid` always contains next-server's PID
2. `runtime/backend.pid` always contains uvicorn's PID  
3. `kill -0 $(cat frontend.pid)` accurately reflects frontend liveness
4. `kill -0 $(cat backend.pid)` accurately reflects backend liveness
5. `kill -- -$(ps -o pgid= -p $(cat frontend.pid))` terminates the full stack
6. `status.sh` never reports STALE for a live service
