# BarkMind — Lifecycle Truthfulness Audit

**Date:** 2026-05-17  
**Trigger:** `status.sh` reporting `frontend PID: STALE` while frontend was live on :3008  
**Status:** RESOLVED

---

## Audit Findings

### Finding 1: `$!` Captures setsid Wrapper, Not the Runtime Process

When bash runs:
```bash
setsid npm run start >> logfile 2>&1 &
FRONTEND_PID=$!
```

`$!` captures the PID of the **`setsid` wrapper process**, not `npm` or `next-server`.

**Why:** When the calling shell (bash) is already a session leader, the `setsid` utility must fork to create a new session. The fork structure is:

```
bash (SID=X, session leader)
  └── setsid wrapper (PID A = $!)
        └── forks → child (PID B) calls setsid(), becomes new session leader
                └── execs npm
                      └── npm spawns next-server
```

The `setsid` wrapper (PID A) exits immediately after fork. `$!` = A = dead wrapper.

The actual npm gets PID B (a new PID that bash never saw). When npm exits or the setsid wrapper exits first, next-server is orphaned with PPID=1.

### Finding 2: The Actual Runtime Process Tree

After `setsid npm run start &`:

```
npm (PID B, PPID=1, PGID=B, SID=B)    ← new session leader
  └── sh -c next start -p 3008 (PID C)
        └── next-server (PID D)        ← canonical runtime, holds :3008
```

- PID A (`$!`) → exits immediately → `kill -0 A` fails → **STALE**
- PID B (npm) → stays alive
- PID D (next-server) → stays alive, holds :3008

### Finding 3: Backend Has Different But Related Behavior

`setsid uvicorn ... &` results in:
```
setsid wrapper (PID A = $!, PPID=bash)   ← stays alive as parent of uvicorn
  └── uvicorn (PID A+1)                  ← actual runtime
```

For uvicorn, the setsid wrapper does not exit immediately — it remains as the parent of uvicorn. `kill -0 $!` succeeds (wrapper alive) → backend showed `running`.

However, `stop.sh` sending SIGTERM to the setsid wrapper would orphan uvicorn without terminating it — the same underlying problem.

### Finding 4: Port-Based PID is the Ground Truth

After the service is confirmed healthy, the process listening on the port is definitively the canonical runtime:

```bash
ss -tlnp | grep ":$PORT " | sed -n 's/.*pid=\([0-9]*\).*/\1/p'
```

For backend: returns uvicorn PID (actual runtime)  
For frontend: returns next-server PID (actual runtime)

---

## Resolution

After each service's readiness check, `start.sh` overwrites the PID file with the actual runtime PID from `ss -tlnp`. This is done for both backend and frontend.

Both `status.sh` and `stop.sh` then operate on the correct PIDs.

---

## Test Results

| Cycle | status.sh backend | status.sh frontend |
|---|---|---|
| Before fix | running (wrapper, fragile) | **STALE** |
| After fix | running (uvicorn) | running (next-server) |

Stop/restart cycles: 2 clean cycles, both ports released, no STALE reported.
