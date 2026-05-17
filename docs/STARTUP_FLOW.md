# BarkMind — Startup Flow

**Date:** 2026-05-17

---

## Startup Sequence

```
./start.sh
│
├── 1. Log startup with timestamp
│
├── 2. Create runtime/ and logs/ directories
│
├── 3. Load .env from project root
│       → Fails fast if .env missing
│
├── 4. Validate dependencies
│       → python3
│       → uvicorn
│       → Warns if psql missing
│
├── 5. Port conflict enforcement
│       → lsof -ti:8108  → exit 1 if occupied
│       → lsof -ti:3008  → exit 1 if occupied
│
├── 6. Stale PID file cleanup
│       → If PID file exists but process is dead → remove file
│       → If PID file exists and process is alive → exit 1 (stop first)
│
├── 7. Media root validation
│       → Create ./media/cases if missing
│       → exit 1 if not writable
│
├── 8. Database connectivity check (asyncpg)
│       → Warning (not exit) if DB unreachable
│
├── 9. Alembic migration check + apply
│       → alembic upgrade head (idempotent)
│       → Warning if alembic not available
│
├── 10. Start backend (setsid uvicorn ... &)
│        → Writes PID to runtime/backend.pid
│        → Appends to logs/backend.log
│
├── 11. Backend health check loop (30s timeout)
│        → curl /health every 1s
│        → exit 1 if process dies before health check passes
│        → Warning if 30s passes without healthy response
│
├── 12. FastAPI lifespan (inside backend):
│        → Seed tags (idempotent)
│        → Seed taxonomy (idempotent)
│        → Mount media files at /media
│        → Attempt Aegis registration (warning only on failure)
│        → Log "BarkMind backend ready"
│
├── 13. Start frontend (if .next/ built)
│        → setsid npm run start &
│        → Writes PID to runtime/frontend.pid
│        → Appends to logs/frontend.log
│        → Frontend readiness check (20s timeout)
│
├── 14. Aegis registration (from start.sh)
│        → POST to http://127.0.0.1:8102/api/apps/register
│        → Log HTTP status code (non-blocking)
│
└── 15. Print startup summary with elapsed time
         → Backend URL, Frontend URL, Docs URL, Logs path
```

---

## FastAPI Lifespan (Backend Internal)

When uvicorn starts the FastAPI app, the async lifespan context runs:

```
async with lifespan(app):
  1. Log "BarkMind backend starting — port {N}"
  2. Create/verify media root directory
  3. Seed behavioral tags (23 tags, idempotent)
  4. Seed behavioral taxonomy (73 terms, idempotent)
  5. Mount /media static files endpoint
  6. POST to Aegis registration (warning on failure)
  7. Log "BarkMind backend ready"
  [yield — server accepts requests]
  8. Log "BarkMind backend shutting down"
```

---

## Shutdown Sequence (stop.sh)

```
./stop.sh
│
├── 1. Read runtime/backend.pid
│       → SIGTERM to PID
│       → Wait 10s for graceful shutdown
│       → SIGKILL if still alive after 10s
│       → Remove PID file
│       → Fallback: kill by port (:8108) if no PID file
│
├── 2. Read runtime/frontend.pid
│       → Same SIGTERM → wait → SIGKILL sequence
│       → Fallback: kill by port (:3008) if no PID file
│
└── 3. Log "BarkMind stopped"
```

---

## Startup Timing (observed)

On the development VM with data already seeded:

| Phase | Duration |
|---|---|
| Dependency check | < 0.5s |
| Port check | < 0.1s |
| DB connectivity | ~0.5s |
| Migration check | ~0.3s |
| Backend process start | ~0.1s |
| Backend health (first response) | 1–3s |
| Frontend start | ~1s |
| Frontend readiness | 2–5s |
| **Total** | **~5–10s** |

On first startup (initial seed):
- Tags seeding: +0.1s
- Taxonomy seeding: +0.1s
- **Total** ~6–11s

---

## Error Exit Codes

| Exit Code | Cause |
|---|---|
| 0 | Success |
| 1 | Dependency missing |
| 1 | .env not found |
| 1 | Port 8108 occupied |
| 1 | Port 3008 occupied |
| 1 | Backend process died before health check |
| 1 | Media root not writable |
| 1 | PID conflict (already running) |

---

## Idempotency

`start.sh` is safe to run multiple times:
- Port check prevents double-starting
- PID file check prevents running two instances
- Alembic `upgrade head` is idempotent (no-op if already current)
- Tag/taxonomy seeding is idempotent (skips existing slugs)
