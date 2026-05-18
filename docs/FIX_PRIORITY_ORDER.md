# BarkMind — Fix Priority Order

**Date:** 2026-05-17

---

## Priority 1: CRITICAL — Applied ✓

### 1a. Systemd Supervision for Frontend (DONE)

**Why:** Aegis's `pkill -f "next-server"` kills the frontend every ~20-30 min. Without supervision, it stays dead permanently.

**Applied:**
```bash
sudo systemctl enable --now barkmind-frontend
# Restart=always in unit file
# Survived pkill test: restarted within 5s
```

### 1b. Systemd Supervision for Backend (DONE)

**Why:** Uvicorn had no supervisor. Any crash → permanent outage.

**Applied:**
```bash
sudo systemctl enable --now barkmind-backend
```

### 1c. Ecosystem Registry Registration (DONE)

**Why:** BarkMind was invisible to Aegis. Ports 3008/8108 were falsely claimed by coreperk.

**Applied:** BarkMind added to `/home/jesse/infra/apps_registry.json` as `active`. coreperk reassigned to 3010/8110.

---

## Priority 2: HIGH — Required Soon

### 2a. Fix Aegis start.sh Line 76

**Why:** The root cause of F1 is still present. `pkill -f "next-server"` in Aegis's start.sh will continue killing ALL next-servers. Systemd mitigates the impact (5s restart) but doesn't eliminate the disruption.

**Action required (in Aegis codebase):**
```bash
# Change (dangerous):
pkill -f "next-server"

# To (scoped kill using Aegis's own PID/port):
# Only kill next-server processes belonging to Aegis
kill -TERM $(cat /path/to/aegis/runtime/frontend.pid)
```

This is a change to the Aegis repository and requires separate review.

### 2b. Close UFW Port 3008

**Why:** next-server binds to `*:3008` (all interfaces) and UFW has `3008 ALLOW Anywhere`. Raw VM traffic bypasses Cloudflare governance.

**Action:**
```bash
sudo ufw delete allow 3008/tcp
# Traffic still works via Cloudflare tunnel
```

**Optional:** Bind Next.js to localhost only:
In `frontend/package.json`: `"start": "next start -p 3008 --hostname 127.0.0.1"`
Then rebuild with `npm run build`.

---

## Priority 3: MEDIUM — Recommended

### 3a. Update status.sh for Systemd Awareness

**Why:** `status.sh` reads `runtime/frontend.pid`. Under systemd management, this file isn't updated by systemd. The script may show stale state.

**Action:** Update status.sh to check `systemctl is-active barkmind-frontend` when PID file is stale:
```bash
if ! kill -0 "$PID" 2>/dev/null; then
  systemctl is-active barkmind-frontend 2>/dev/null | grep -q "active" && \
    echo "managed by systemd" || echo "STALE"
fi
```

### 3b. Add More Test Data

**Why:** The platform has 1 case. All pages appear empty to new users who don't know there's real data.

**Action:** Create sample cases via the API with various behavioral scenarios to demonstrate platform capabilities.

### 3c. Update NEXT_PUBLIC_API_URL Build

**Why:** `NEXT_PUBLIC_API_URL` in the frontend is correct (`https://barkmind-api.jesseboudreau.com`) but it's set in `.env` which is used for the dev build. The production build needs this to be baked in.

**Note:** Currently the API client doesn't use `NEXT_PUBLIC_API_URL` for actual API calls (uses `/api-backend/*` proxy). This is a display/link variable. Verify it's used correctly.

---

## Priority 4: LOW — Future Consideration

### 4a. Reboot Persistence Test

**Why:** Both systemd services are enabled, so they should start on reboot. This has not been tested (can't reboot production VM trivially).

**Verify when safe:** `sudo reboot` → check `systemctl status barkmind-backend barkmind-frontend`.

### 4b. Log Rotation

**Why:** `logs/backend.log` and `logs/frontend.log` will grow unboundedly. SystemD currently appends to them.

**Action:** Add logrotate configuration for `/home/jesse/infra/apps/BarkMind/logs/*.log`.

### 4c. Frontend Build Rebuild for Production Hostname

**Why:** The Next.js build was done in a dev context. A clean build with `NEXT_PUBLIC_API_URL=https://barkmind-api.jesseboudreau.com` baked in may improve behavior.

**Action:** 
```bash
cd frontend && npm run build
sudo systemctl restart barkmind-frontend
```

---

## Summary Table

| # | Action | Priority | Status | Time Required |
|---|---|---|---|---|
| 1a | Systemd frontend supervision | CRITICAL | **DONE** | — |
| 1b | Systemd backend supervision | CRITICAL | **DONE** | — |
| 1c | Ecosystem registry | CRITICAL | **DONE** | — |
| 2a | Fix Aegis pkill (Aegis repo) | HIGH | OPEN | 30min |
| 2b | Close UFW port 3008 | HIGH | OPEN | 2min |
| 3a | Update status.sh | MEDIUM | OPEN | 20min |
| 3b | Add test data | MEDIUM | OPEN | 30min |
| 3c | Verify NEXT_PUBLIC_API_URL | MEDIUM | OPEN | 5min |
| 4a | Reboot persistence test | LOW | OPEN | 10min |
| 4b | Log rotation | LOW | OPEN | 15min |
| 4c | Fresh prod build | LOW | OPEN | 10min |
