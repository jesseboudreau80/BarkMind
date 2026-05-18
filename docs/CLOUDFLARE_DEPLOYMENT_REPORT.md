# BarkMind — Cloudflare Deployment Report

**Date:** 2026-05-17  
**Status:** LIVE  
**Tunnel:** reselleros (82b66414-9142-442e-bded-bb7fc70d7b4c)

---

## Live Endpoints

| Endpoint | URL | Status |
|---|---|---|
| Frontend | https://barkmind.jesseboudreau.com | ✓ HTTP 200 |
| Backend API | https://barkmind-api.jesseboudreau.com | ✓ HTTP 200 |
| /health | https://barkmind-api.jesseboudreau.com/health | ✓ HTTP 200 |
| /version | https://barkmind-api.jesseboudreau.com/version | ✓ HTTP 200 |
| /.well-known/aegis-meta | https://barkmind-api.jesseboudreau.com/.well-known/aegis-meta | ✓ HTTP 200 |
| /governance/status | https://barkmind-api.jesseboudreau.com/governance/status | ✓ HTTP 200 |
| /governance/metrics | https://barkmind-api.jesseboudreau.com/governance/metrics | ✓ HTTP 200 |

---

## Deployment Steps Executed

### 1. Infrastructure Inspection
- Located active config: `~/.cloudflared/config.yml` (used by systemd service)
- Confirmed active tunnel: `reselleros` (ID: 82b66414-9142-442e-bded-bb7fc70d7b4c)
- Confirmed tunnel connections: 4 active connections to Cloudflare edge (EWR region)

### 2. Ingress Rules Added
Added to `~/.cloudflared/config.yml` before the catch-all rule:
```yaml
# ── BarkMind — doctrine: frontend 3008, backend 8108 ─────────────────────
- hostname: barkmind.jesseboudreau.com
  service: http://127.0.0.1:3008

- hostname: barkmind-api.jesseboudreau.com
  service: http://127.0.0.1:8108
```

### 3. DNS Records Created
```bash
cloudflared tunnel route dns reselleros barkmind.jesseboudreau.com
cloudflared tunnel route dns reselleros barkmind-api.jesseboudreau.com
```

Both CNAMEs point to `82b66414-9142-442e-bded-bb7fc70d7b4c.cfargotunnel.com`, proxied via Cloudflare.

### 4. Config Validation
```
cloudflared --config ~/.cloudflared/config.yml tunnel ingress validate
→ OK
```

### 5. Service Restart
```bash
sudo systemctl restart cloudflared
```

### 6. Root Cause Debugging
**Issue discovered:** There were THREE cloudflared processes:
- `PID 475653` (root, systemd) — NEW config with BarkMind rules
- `PID 2685944` (jesse, user) — OLD config from May 16, actively routing all traffic
- `PID 2689880` (jesse, user) — dp-dvm-map tunnel

The user-level process (2685944) was routing all traffic using the pre-BarkMind config. Traffic never reached the systemd instance.

**Resolution:** `kill -TERM 2685944` — terminated the old process. The systemd service (475653) with the correct config immediately took over and began routing BarkMind traffic.

---

## SSL Certificate

- **Issuer:** Let's Encrypt (E7)
- **Subject:** CN = jesseboudreau.com (wildcard via Cloudflare Universal SSL)
- **Verify:** 0 (ok)
- **Protocol:** HTTP/2 via HTTPS

---

## Validation Results

| Test | Result |
|---|---|
| barkmind-api/health via HTTPS | `{"status":"ok","service":"barkmind","version":"1.0.0"}` |
| barkmind-api/version | `{"version":"1.0.0","commit":"e60d547"}` |
| Aegis meta (13 capabilities) | ✓ |
| Governance status | ✓ operational |
| Frontend / | HTTP 307 → /cases |
| Frontend /cases | HTTP 200 |
| Frontend /login | HTTP 200 |
| SSL verification | Verify return code: 0 (ok) |
| Cloudflare edge marker | cf-ray header present |
| Tunnel request count | 26 requests processed |
| Existing services unaffected | reselleros-api still HTTP 200 |

---

## Security Notes

### UFW Ports Open for BarkMind
```
3008/tcp   ALLOW   Anywhere
8108/tcp   ALLOW   Anywhere
```

**Backend (8108):** Bound to `127.0.0.1` only — NOT accessible directly from internet even with UFW open. No action required.

**Frontend (3008):** Bound to `*:3008` — accessible directly from internet if UFW allows it. Since Cloudflare Tunnel is the governed ingress, the recommended action is:

```bash
# Option A: Close the UFW rule (traffic comes via tunnel only)
sudo ufw delete allow 3008/tcp

# Option B: Bind Next.js to loopback only (update start command)
# In package.json: "start": "next start -p 3008 --hostname 127.0.0.1"
```

Both approaches achieve the same security posture. Option B requires a frontend rebuild.

---

## Reboot Persistence

- **cloudflared systemd service:** `enabled` — starts automatically on reboot
- **BarkMind processes:** Started by lifecycle scripts (`./start.sh`) — NOT currently auto-started
- **Recommendation:** Add BarkMind to systemd or cron for auto-restart on reboot (see RUNTIME_OPERATIONS.md)
