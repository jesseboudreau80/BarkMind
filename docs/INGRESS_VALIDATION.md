# BarkMind — Ingress Validation

**Date:** 2026-05-17  
**Status:** ALL CHECKS PASSING

---

## Backend API Validation

### Governance Endpoints

| Endpoint | HTTP | Response |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","service":"barkmind","version":"1.0.0"}` |
| `GET /whoami` | 200 | Runtime identity |
| `GET /version` | 200 | `{"version":"1.0.0","commit":"e60d547"}` |
| `GET /.well-known/aegis-meta` | 200 | 13 capabilities declared |
| `GET /governance/status` | 200 | `operational` |
| `GET /governance/metrics` | 200 | Platform metrics |

### Application Endpoints

| Endpoint | HTTP | Notes |
|---|---|---|
| `GET /tags` | 200 | 73 taxonomy terms returned |
| `GET /cases` | 200 | Case list with pagination |
| `POST /auth/login` | 200 | JWT auth working |

---

## Frontend Validation

| Route | HTTP | Notes |
|---|---|---|
| `/` | 307 → /cases | Redirect working |
| `/cases` | 200 | Case list renders |
| `/tags` | 200 | Tag browser renders |
| `/about` | 200 | About page renders |
| `/login` | 200 | Login form renders |
| `/register` | 200 | Register form renders |

---

## SSL/TLS Validation

```
Server: barkmind-api.jesseboudreau.com
Port: 443 (HTTPS)
Protocol: TLS 1.3
Certificate Subject: CN = jesseboudreau.com
Certificate Issuer: Let's Encrypt E7
Verify return code: 0 (ok)
```

Cloudflare Universal SSL is active. HTTPS is enforced via Cloudflare's edge.

---

## Cloudflare Edge Markers

Every response from `barkmind-api.jesseboudreau.com` includes:
```
server: cloudflare
cf-ray: <ray-id>-EWR
cf-cache-status: DYNAMIC
```

These confirm:
- Traffic is passing through Cloudflare's edge (not direct to VM)
- Requests are served dynamically (not from cache)
- Connected to New York/Newark edge nodes (EWR)

---

## Tunnel Activity

```
cloudflared_tunnel_total_requests: 26
```

26 requests processed through tunnel since last restart, confirming the tunnel is actively carrying traffic.

---

## Aegis Compatibility

The `/.well-known/aegis-meta` endpoint responds with:
```json
{
  "app": "barkmind",
  "backend_port": 8108,
  "frontend_port": 3008,
  "capabilities": [...13 capabilities...],
  "governance_endpoints": {
    "status": "/governance/status",
    "metrics": "/governance/metrics",
    ...
  }
}
```

BarkMind remains discoverable to Aegis through the public hostname. Governance endpoints are accessible without authentication for Aegis polling.

---

## What Was Not Tested

- WebSocket compatibility (Next.js supports it; cloudflared supports HTTP upgrade)
- Media file upload via HTTPS (would work via tunnel; file size limits apply)
- High-concurrency load testing (beyond scope for MVP)
- IPv6 routing (Cloudflare handles this transparently)
