# BarkMind — Production Root Cause Analysis

**Date:** 2026-05-17  
**Investigation method:** Layer-by-layer empirical tracing. No assumptions trusted.

---

## Executive Summary

BarkMind was non-functional because its frontend process (next-server) was being periodically killed by Aegis's startup script (`pkill -f "next-server"` — a VM-wide kill). BarkMind was not in the ecosystem registry, so it was killed but never restarted. This caused permanent spinners on all frontend pages because the API proxy (`/api-backend/*`) returned 502.

---

## Root Cause 1: Aegis Kills All next-server Processes

**File:** `/home/jesse/infra/apps/aegis/start.sh`, lines 76-78

```bash
pkill -f "next-server"              2>/dev/null || true
pkill -f "next start"               2>/dev/null || true
pkill -f "next build"               2>/dev/null || true
```

When Aegis restarts (which happens regularly during ecosystem management), it kills **every** next-server process on the VM. This includes BarkMind's frontend.

**Why this was missed:** Aegis's `stop.sh` has a comment saying NOT to use pkill broadly. But `start.sh` does it anyway. The kill is in start.sh, not stop.sh — it was cleaning up before launching Aegis's own processes.

---

## Root Cause 2: BarkMind Not in Ecosystem Registry

**File:** `/home/jesse/infra/apps_registry.json`

BarkMind was not registered. The registry assigned ports 3008/8108 to "coreperk" (a planned, never-built app). When Aegis killed all next-servers:
- Aegis restarted its own managed apps (all have registry entries)
- BarkMind was not in the registry → not restarted
- coreperk has no code → no coreperk frontend to start either

Result: port 3008 was empty after every Aegis restart.

---

## Root Cause 3: No Process Supervision for BarkMind

BarkMind's frontend ran as an orphaned `setsid npm run start` process. There was no supervisor watching it. When killed, nothing restarted it.

The backend (uvicorn) also had no supervisor but happened to not be targeted by Aegis's pkill (which targeted next-server patterns, not uvicorn).

---

## Evidence Chain

| Time | Event |
|---|---|
| 19:00:47 | BarkMind frontend started (PID 495080/495093) |
| 19:20:23 | Aegis restart initiated |
| 19:20:xx | Aegis `start.sh` runs `pkill -f "next-server"` |
| 19:20:xx | BarkMind frontend (PID 495093) killed — no log entry |
| 19:20:xx | Other apps restarted by Aegis (PIDs 517xxx) |
| 19:21:25 | cloudflared logs: "dial tcp 127.0.0.1:3008: connect: connection refused" |
| 19:21+ | All `/api-backend/*` requests return 502 |
| 19:21+ | All case pages show permanent spinner |

---

## Secondary Findings

### Finding A: Frontend serves spinner-only HTML (expected)

The cases page is a Client Component (SWR-based). SSR renders a loading spinner. After JavaScript hydrates and SWR fetches, cases load. This is correct Next.js behavior — not a bug.

**But:** when the `/api-backend/cases` SWR call returns 502 (because Next.js is dead), the spinner is permanent. The spinner itself is not the bug; the 502 is.

### Finding B: Backend was healthy throughout

Uvicorn on :8108 was never killed. All backend API calls (`barkmind-api.jesseboudreau.com/*`) continued working. The failure was entirely in the frontend layer.

### Finding C: Cloudflare tunnel routing was correct

The tunnel correctly routed:
- `barkmind-api.jesseboudreau.com` → :8108 (always worked)
- `barkmind.jesseboudreau.com` → :3008 (worked when frontend was alive)

The 502 responses during frontend outage came from cloudflared's accurate error handling: "Unable to reach the origin service."

---

## What Was Operational

| Component | Status |
|---|---|
| DNS routing | ✓ Always correct |
| SSL certificates | ✓ Always valid |
| Cloudflare tunnel | ✓ Always routing |
| Backend API | ✓ Always healthy |
| Frontend HTML | ✓ Served when process alive |
| API proxy (`/api-backend/*`) | ✗ Failed when frontend dead |
| Client-side data loading | ✗ Failed (502 from proxy) |
| Auth flow | ✓ When frontend alive |

---

## Fix Applied

1. **Systemd supervision installed:**
   - `barkmind-backend.service` — uvicorn with `Restart=always`
   - `barkmind-frontend.service` — next-server with `Restart=always`
   - Both `enabled` — survive reboots
   - Frontend restarted within 5s after pkill (tested and verified)

2. **Ecosystem registry updated:**
   - BarkMind added to `apps_registry.json` as `active` service
   - coreperk reassigned to 3010/8110 (still planned, never built)
   - Port doctrine updated

3. **Governance alignment confirmed:**
   - BarkMind is now a registered ecosystem service
   - Port ownership documented correctly
