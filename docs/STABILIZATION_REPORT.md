# BarkMind — Stabilization Report

**Date:** 2026-05-17  
**Status:** COMPLETE

---

## Port Normalization

BarkMind has been normalized to its permanent canonical ports:

| Component | Port |
|---|---|
| Backend (FastAPI) | **8108** |
| Frontend (Next.js) | **3008** |

Ports 8107/3007 remain with Aegis Lite and are not touched.

### Files Updated

| File | Change |
|---|---|
| `.env` | `BACKEND_PORT=8108`, `FRONTEND_PORT=3008` |
| `.env.example` | Same |
| `backend/app/config.py` | Default `backend_port=8108`, `frontend_port=3008` |
| `frontend/next.config.ts` | Default `BACKEND_INTERNAL_URL=http://127.0.0.1:8108` |
| `frontend/.env.local` | `BACKEND_INTERNAL_URL=http://127.0.0.1:8108` |
| `frontend/package.json` | `next dev -p 3008`, `next start -p 3008` |
| `start.sh` | `BACKEND_PORT=8108`, `FRONTEND_PORT=3008` |
| `stop.sh` | Port references updated |
| `status.sh` | Port references updated |
| `config/aegis.manifest.json` | Ports updated |
| `config/aegis.runtime.yml` | Ports updated |
| `config/apps_registry_entry.json` | Ports updated |
| `CLAUDE.md` | Canonical port declaration updated |

---

## Lifecycle Script Improvements

### `start.sh` — Full Rewrite

- Structured timestamped logging (`[BARKMIND HH:MM:SS]`)
- Dependency validation (python3, uvicorn)
- Database connectivity check via asyncpg
- Automatic pending migration check + apply
- Stale PID file cleanup
- Backend health check with process death detection (not just timeout)
- Frontend readiness check (waits for HTTP response)
- Aegis registration with HTTP status code reporting
- Startup timing metric in summary

### `stop.sh` — Improved

- Port-based fallback kill (if no PID file, kills by port occupancy)
- Graceful SIGTERM → SIGKILL escalation with status messages
- Stale PID file cleanup

### `status.sh` — Improved

- Full endpoint display (API, UI, Docs)
- Health check parses JSON response (shows version)
- Clear visual structure

### `restart.sh` — Updated

- 2-second pause between stop and start (port release time)
- Timestamped log output

---

## Test Results

| Test | Result |
|---|---|
| Backend starts on :8108 | PASS |
| `whoami` reports `port=8108` | PASS |
| `/.well-known/aegis-meta` reports `backend_port=8108 frontend_port=3008` | PASS |
| Governance status: `operational`, 10 capabilities | PASS |
| Aegis meta: 13 capabilities + governance_endpoints | PASS |
| Telemetry events: returns events | PASS |
| Telemetry summary: counts by type | PASS |
| Telemetry ops: pending/escalated counts | PASS |
| Analytics summary: cases/annotations/experts | PASS |
| Export JSON: 1 case, status=locked | PASS |
| Export NDJSON: 2 annotation lines | PASS |
| Export CSV: correct header row | PASS |
| Export history: 4 logged jobs | PASS |
| Dataset lineage: annotations + provenance | PASS |
| Dataset snapshots list: 1 snapshot | PASS |
| Image upload: `status=ready` thumbnails sm/md/lg | PASS |
| Image dimensions: 400x300 extracted | PASS |
| Security: HTML-as-JPEG → HTTP 415 | PASS |
| Governance compliance checklist: all true | PASS |
| Backend restart: clean start on :8108 | PASS |
| Status script: detects running backend | PASS |
| Frontend build: 15/15 routes clean | PASS |
| Clean DB migration test: all 5 migrations from scratch | PASS |
| Aegis Lite on :8107: UNAFFECTED | PASS |
| No 8107/3007 in operational files: CLEAN | PASS |

All 23 tests passed.

---

## Known Issues

See `docs/KNOWN_LIMITATIONS.md` for the complete list.

Key items:
1. Aegis registration returns 404 (Aegis API path mismatch — non-blocking)
2. Frontend is started separately from backend (no unified process supervisor)
3. Cloudflare tunnel not yet configured for :8108/:3008 hostnames
