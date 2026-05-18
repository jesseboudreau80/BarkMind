# BarkMind — Operational Reality Report

**Date:** 2026-05-17  
**Investigation:** Full layer-by-layer empirical audit

---

## Current Operational State (After Fixes)

| Layer | Status | Method Verified |
|---|---|---|
| Backend process (uvicorn) | **RUNNING** — systemd managed | `ss -tlnp`, `/health` |
| Frontend process (next-server) | **RUNNING** — systemd managed | `ss -tlnp`, HTTP 307 |
| Backend local API | **WORKING** | `curl http://127.0.0.1:8108/health` |
| Frontend local proxy | **WORKING** | `curl http://127.0.0.1:3008/api-backend/health` |
| DNS (barkmind.jesseboudreau.com) | **RESOLVING** | `dig` returns Cloudflare IPs |
| Cloudflare tunnel routing | **ACTIVE** | cloudflared ingress rule #17/#18 match |
| SSL certificates | **VALID** | Let's Encrypt, verify code 0 |
| Backend public API | **WORKING** | `https://barkmind-api.jesseboudreau.com/health` → 200 |
| Frontend proxy via Cloudflare | **WORKING** | `https://barkmind.jesseboudreau.com/api-backend/health` → 200 |
| Frontend pages | **WORKING** | All 6 routes → HTTP 200 |
| Auth login flow | **WORKING** | JWT returned via public domain |
| Cases data load | **WORKING** | Proxy returns 1 case |
| Tags load | **WORKING** | 23 tags returned |
| Taxonomy load | **WORKING** | 73 terms returned |
| Media serving | **WORKING** — API domain | `barkmind-api.jesseboudreau.com/media/...` → 200 |
| Ecosystem registry | **REGISTERED** | barkmind in apps_registry.json |
| Systemd supervision | **ACTIVE** | `Restart=always`, survives pkill |

---

## What Was Broken (Pre-Fix)

### Primary Failure: Frontend Dead, Spinner Permanent

**Symptom:** All pages showed permanent loading spinners. API calls returned 502.

**Cause:** Aegis's `start.sh` runs `pkill -f "next-server"` which killed BarkMind's frontend. BarkMind had no supervisor, so it stayed dead.

**Detection:** cloudflared logs at 19:21:25 showed `connect: connection refused` on :3008.

### Secondary Failure: Not in Ecosystem Registry

**Symptom:** BarkMind's ports were registered to "coreperk" (a planned, unbuilt app).

**Cause:** BarkMind was never added to `/home/jesse/infra/apps_registry.json`. Port ownership was undocumented.

**Detection:** `grep` of apps_registry.json showed `coreperk` had ports 3008/8108; barkmind was absent.

---

## Layer-by-Layer Reality

### Layer 1: Process (empirically verified)
- uvicorn (backend): systemd-managed, PID 528851, :8108 ✓
- next-server (frontend): systemd-managed, PID 529899, :3008 ✓
- cloudflared: systemd-managed, PID 475653, 4 tunnel connections ✓

### Layer 2: Local Runtime
- `curl http://127.0.0.1:8108/health` → `{"status":"ok"}` ✓
- `curl http://127.0.0.1:3008/api-backend/health` → `{"status":"ok"}` ✓
- `curl http://127.0.0.1:3008/cases` → HTTP 307 → /cases ✓

### Layer 3: Cloudflare
- DNS: A records for both domains → Cloudflare proxy IPs ✓
- Ingress: rules #17 (barkmind.com→:3008) and #18 (barkmind-api→:8108) match ✓
- SSL: `Verify return code: 0 (ok)` ✓
- `cf-ray` header present on every response ✓

### Layer 4: Frontend/API Integration
- Browser API calls go to `/api-backend/*` (same-origin, proxied by Next.js) ✓
- Proxy rewrites to `http://127.0.0.1:8108/*` ✓
- CORS: `Access-Control-Allow-Origin: https://barkmind.jesseboudreau.com` ✓

### Layer 5: User Flows
- Login: JWT issued ✓
- Cases page: data loads (after JavaScript hydrates) ✓
- Tags page: 23 tags rendered ✓
- Static assets: JS chunks HTTP 200 ✓

---

## Remaining Risks

### Risk 1: Aegis Still Has Dangerous pkill

`/home/jesse/infra/apps/aegis/start.sh` line 76 still runs `pkill -f "next-server"`. This will kill BarkMind's frontend but systemd (`Restart=always`) will bring it back within 5 seconds. **Workaround is in place. Root cause in Aegis is not fixed.**

### Risk 2: Single Case in Database

Only 1 case exists (from Phase 1 testing). The platform appears sparse. This is a data issue, not a technical failure.

### Risk 3: Frontend Binds to All Interfaces

Next.js binds to `*:3008` (all interfaces). UFW has `3008/tcp ALLOW Anywhere`. This means the frontend is publicly accessible on the VM's raw IP. Not a security risk (frontend is public anyway) but bypasses Cloudflare governance. Recommend: `sudo ufw delete allow 3008/tcp` since all ingress should go via Cloudflare.

### Risk 4: `next-server` PID vs npm PID in Lifecycle Scripts

The `start.sh` now correctly resolves the actual next-server PID after startup. But the systemd service supersedes the lifecycle scripts for process management. The `runtime/frontend.pid` file may not be updated by systemd. Running `./status.sh` may show stale state when using systemd management.
