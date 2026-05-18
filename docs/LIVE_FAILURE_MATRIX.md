# BarkMind — Live Failure Matrix

**Date:** 2026-05-17

---

## Failure Classification

| ID | Failure | Severity | Layer | Root Cause | Status |
|---|---|---|---|---|---|
| F1 | Frontend killed by Aegis pkill | CRITICAL | Process | Aegis start.sh pkill -f "next-server" | **FIXED** (systemd Restart=always) |
| F2 | BarkMind not in ecosystem registry | HIGH | Governance | Never registered | **FIXED** (barkmind added to apps_registry.json) |
| F3 | Port 3008/8108 attributed to coreperk | HIGH | Governance | Registry showed wrong owner | **FIXED** (coreperk reassigned to 3010/8110) |
| F4 | Old cloudflared process shadowing new config | MEDIUM | Infra | User-level process from May 16 had old config | **FIXED** (killed during deployment, systemd is sole authority) |

---

## Per-Layer Failure Detail

### Process Layer

| Component | Failure | Impact | Fix |
|---|---|---|---|
| next-server | Killed by Aegis pkill, no supervisor | Frontend unavailable | systemd barkmind-frontend.service |
| uvicorn | No supervisor | Would die on crash | systemd barkmind-backend.service |
| cloudflared | Duplicate instances | Traffic routing inconsistent | Single systemd instance confirmed |

### Application Layer

| Endpoint | Status When Frontend Dead | Status When Frontend Alive |
|---|---|---|
| `/` (frontend) | HTTP 502 | HTTP 307 ✓ |
| `/cases` | HTTP 502 | HTTP 200 ✓ |
| `/api-backend/cases` | HTTP 502 | HTTP 200 ✓ |
| `barkmind-api.jesseboudreau.com/health` | HTTP 200 ✓ | HTTP 200 ✓ |
| SWR data loads | Permanent spinner | Data appears ✓ |

### Governance Layer

| Item | Failure | Status |
|---|---|---|
| apps_registry.json | BarkMind absent | Fixed — barkmind entry added |
| Port ownership | 3008/8108 → coreperk | Fixed — 3008/8108 → barkmind |
| Cloudflare ingress | Not configured | Fixed — both CNAMEs and ingress rules active |
| Systemd enablement | None | Fixed — both services enabled |

---

## What Never Failed

| Component | Reality |
|---|---|
| Backend API | Running continuously since 17:57 |
| DNS routing | Correct from first `route dns` command |
| SSL certificates | Valid throughout |
| Cloudflare tunnel connections | 4 active connections, stable |
| Database | PostgreSQL, all 22 tables present |
| Behavioral taxonomy | 73 terms seeded |
| Auth (when frontend alive) | JWT flow working |

---

## Failure Frequency Analysis

| Failure Type | Estimated Recurrence | Trigger |
|---|---|---|
| Frontend killed | Every Aegis restart (~every 20-30 min) | `pkill -f "next-server"` |
| Recovery time (pre-fix) | Never (no supervisor) | Manual restart required |
| Recovery time (post-fix) | ~5 seconds | systemd Restart=always |
| Backend crash | Infrequent | systemd restarts within 5s |

---

## Environment Hazards

| Hazard | Risk Level | Notes |
|---|---|---|
| Aegis pkill -f "next-server" | HIGH | Kills ALL next-servers. Fixed by systemd supervision. |
| Multiple cloudflared instances | MEDIUM | Resolved — one systemd-managed instance |
| VM memory pressure | LOW | 9GB free, 11GB used across all apps |
| No backup/HA | LOW | Single VM, single process per service |
