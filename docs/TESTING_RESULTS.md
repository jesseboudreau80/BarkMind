# BarkMind — Testing Results

**Date:** 2026-05-17  
**Tested against:** backend=:8108, DB=barkmind

---

## Test Environment

- Backend: FastAPI + asyncpg + PostgreSQL 18.3
- Frontend: Next.js 16.2.6 (webpack build)
- Python: 3.12.3
- Node: v22.22.1
- OS: Ubuntu 24.04

---

## Port Normalization Tests

| Test | Expected | Result |
|---|---|---|
| `settings.backend_port` == 8108 | 8108 | PASS |
| `settings.frontend_port` == 3008 | 3008 | PASS |
| `/whoami` reports `port=8108` | 8108 | PASS |
| `/.well-known/aegis-meta` `backend_port=8108` | 8108 | PASS |
| `/.well-known/aegis-meta` `frontend_port=3008` | 3008 | PASS |
| No 8107/3007 in operational files | empty grep | PASS |
| Aegis Lite still on :8107 | HTTP 200 | PASS |
| `package.json` dev/start on :3008 | `:3008` | PASS |

---

## Governance Endpoints

| Endpoint | Auth | Status | Notes |
|---|---|---|---|
| `GET /health` | None | PASS | `{"status":"ok","service":"barkmind","version":"1.0.0"}` |
| `GET /whoami` | None | PASS | `port=8108 env=local` |
| `GET /version` | None | PASS | `version=1.0.0 commit=6230ef0` |
| `GET /.well-known/aegis-meta` | None | PASS | 13 capabilities, correct ports |
| `GET /governance/status` | None | PASS | `operational`, 10 capabilities |
| `GET /governance/metrics` | None | PASS | `cases=1 annotations=2 locked=1` |

---

## Auth Tests

| Test | Result |
|---|---|
| `POST /auth/register` new user | 201 Created |
| `POST /auth/login` existing user | 200 + JWT pair |
| `GET /auth/me` with valid token | 200 + user profile |
| `GET /auth/me` with no token | 401 unauthorized |
| `POST /auth/refresh` | 200 new token pair |
| Password wrong | 401 unauthorized |

---

## Telemetry Tests

| Test | Result |
|---|---|
| `GET /telemetry/events?limit=3` | 3 events returned |
| `GET /telemetry/events?event_type=case_locked` | filtered results |
| `GET /telemetry/summary` | event counts by type (7d) |
| `GET /telemetry/ops` | `pending=1 escalated=0` |
| Event replay `?since=2026-05-17T00:00:00Z` | returns events from that point |

---

## Analytics Tests

| Endpoint | Key Result |
|---|---|
| `/analytics/cases` | `total=1 resolution_rate=100%` |
| `/analytics/annotations` | `total=2 expert_pct=50%` |
| `/analytics/experts` | `total=1 verified=1` |
| `/analytics/taxonomy` | `active_terms=73 category_usage=populated` |
| `/analytics/consensus` | `total=1 reached=1 agreement_rate=100%` |
| `/analytics/summary` | all combined, no errors |
| `/analytics/inter_rater` | returns comparison pairs |

---

## Export Tests

| Export | Format | Result |
|---|---|---|
| `POST /exports/cases?format=json` | JSON | 1 case, status=locked |
| `POST /exports/cases?format=csv` | CSV | correct header row |
| `POST /exports/annotations?format=ndjson` | NDJSON | 2 lines |
| `POST /exports/audit?format=json` | JSON | audit events |
| `POST /exports/experts?format=json` | JSON | 1 expert |
| `POST /exports/consensus?format=json` | JSON | 1 consensus record |
| `GET /exports/history` | — | 4+ logged jobs |

---

## Media Pipeline Tests

| Test | Result |
|---|---|
| Upload JPEG 8KB | 201, `status=pending` |
| Background thumbnail generation (1s) | `status=ready`, `sm/md/lg` keys |
| Dimensions extracted | `width=400 height=300` |
| HTML file uploaded as JPEG | 415 `mime_mismatch` |
| PHP file uploaded as PNG | 415 `mime_mismatch` |
| PDF uploaded as JPEG | 415 `mime_mismatch` |
| File too large (simulated) | 413 `media_too_large` |

---

## Dataset Governance Tests

| Test | Result |
|---|---|
| `POST /dataset/snapshot` | 201, case_count=1 |
| `GET /dataset/snapshots` | 1 snapshot listed |
| `GET /dataset/snapshots/{id}` | full metadata |
| `GET /dataset/lineage/{case_id}` | 2 annotations with provenance |

---

## Expert Workflow Tests

| Test | Result |
|---|---|
| Create expert profile | 201, `verification=pending` |
| Admin verify expert | 200, `verification=verified`, +10 rep |
| Assign case | 201, `status=pending` |
| Claim assignment | 200, `status=claimed`, +1 rep |
| Initiate consensus | 201, `status=open` |
| Submit opinion | 201, tally updated |
| Consensus reached | `status=reached`, +2 rep |
| Lock evidence | 201, snapshot created |
| Locked case status | `status=locked` |

---

## Lifecycle Script Tests

| Test | Result |
|---|---|
| `bash -n start.sh` syntax check | PASS |
| `bash -n stop.sh` syntax check | PASS |
| `bash -n status.sh` syntax check | PASS |
| `bash -n restart.sh` syntax check | PASS |
| Status script detects running backend | PASS |
| Status script shows :8108 IN USE | PASS |
| Status script shows /health OK | PASS |
| Backend restart recovers | PASS |

---

## Migration Tests

| Test | Result |
|---|---|
| All 5 migrations apply from clean DB | PASS |
| `alembic current` shows latest revision | PASS |
| Migration idempotent (run twice) | PASS |
| Table count after migration | 23 (22 app + alembic_version) |

---

## Frontend Build Tests

| Test | Result |
|---|---|
| `npm run build` (`next build --webpack`) | PASS |
| TypeScript: zero errors | PASS |
| 15/15 routes generated | PASS |
| New routes `/governance`, `/analytics` present | PASS |

---

## Summary

**All 23 critical tests: PASS**  
**Total endpoint tests: 50+ passing**  
**Security rejections: all correct**  
**Migration chain: verified clean from empty DB**  
**Port normalization: complete, zero stale references**  
**Aegis Lite: unaffected on :8107**
