# BarkMind — Domain Routing

**Date:** 2026-05-17

---

## Production Domains

| Purpose | Domain | Internal |
|---|---|---|
| Frontend | `https://barkmind.jesseboudreau.com` | `http://127.0.0.1:3008` |
| Backend API | `https://barkmind-api.jesseboudreau.com` | `http://127.0.0.1:8108` |

---

## Request Flow

```
User browser
  │
  ▼ HTTPS request to barkmind.jesseboudreau.com
  │
Cloudflare Edge (EWR region)
  │ SSL termination
  │ DDoS protection
  │ WAF filtering
  │
  ▼ Tunnel: 82b66414...cfargotunnel.com
  │
cloudflared (PID 475653, root, systemd)
  │ Config: ~/.cloudflared/config.yml
  │ Rule #17: barkmind.jesseboudreau.com → http://127.0.0.1:3008
  │
  ▼ HTTP/1.1 to 127.0.0.1:3008
  │
next-server (Next.js 16 App Router)
  └── Serves frontend: /, /cases, /tags, /login, etc.
```

```
User / API client
  │
  ▼ HTTPS request to barkmind-api.jesseboudreau.com/health
  │
Cloudflare Edge
  │
  ▼ Tunnel
  │
cloudflared
  │ Rule #18: barkmind-api.jesseboudreau.com → http://127.0.0.1:8108
  │
  ▼ HTTP/1.1 to 127.0.0.1:8108
  │
uvicorn (FastAPI + SQLAlchemy)
  └── Returns JSON responses
```

---

## DNS Resolution Chain

```
barkmind.jesseboudreau.com
  └── CNAME → 82b66414-9142-442e-bded-bb7fc70d7b4c.cfargotunnel.com
                └── Proxied by Cloudflare
                      └── Returns: 172.67.139.93, 104.21.57.5 (Cloudflare anycast IPs)

barkmind-api.jesseboudreau.com
  └── CNAME → 82b66414-9142-442e-bded-bb7fc70d7b4c.cfargotunnel.com
                └── Proxied by Cloudflare
                      └── Returns: 172.67.139.93, 104.21.57.5 (Cloudflare anycast IPs)
```

External DNS tools (e.g., `dig`) show Cloudflare's proxy IPs, not the tunnel CNAME target. This is normal behavior for orange-cloud proxied records.

---

## API URL Configuration

### Frontend .env

```
NEXT_PUBLIC_API_URL=https://barkmind-api.jesseboudreau.com
```

This is used for display/link generation. The frontend's API proxy (`/api-backend/*`) routes internally via `BACKEND_INTERNAL_URL=http://127.0.0.1:8108`.

### CORS Configuration

Backend CORS allows:
- `https://barkmind.jesseboudreau.com` (production)
- `http://127.0.0.1:3008` (local development)

---

## Port Summary

| Port | Process | Bind Address | External Access |
|---|---|---|---|
| 8108 | uvicorn (FastAPI) | `127.0.0.1` | Via tunnel only |
| 3008 | next-server (Next.js) | `*` (all) | Via tunnel (recommended) |

**Note:** next-server binds to all interfaces. UFW rule `3008 ALLOW Anywhere` currently allows direct access. Since both apps are public-facing, this is not a security risk, but closing the UFW rule enforces all traffic goes through governed Cloudflare ingress.

---

## Future Cloudflare Configuration

When Cloudflare Tunnel ingress supports HTTPS origins (for internal mTLS):
```yaml
# Future: encrypted internal communication
- hostname: barkmind-api.jesseboudreau.com
  service: https://127.0.0.1:8108
  originRequest:
    tlsTimeout: 10s
    caPool: /path/to/internal-ca.pem
```

For MVP, HTTP to loopback is secure — the data never leaves the VM unencrypted.

---

## Cloudflare-Specific Features Active

| Feature | Status |
|---|---|
| Universal SSL (wildcard cert) | ✓ Active |
| HTTP/2 | ✓ Active |
| Cloudflare WAF | Active (Free tier rules) |
| DDoS mitigation | ✓ Active |
| Bot management | Active |
| Cache | DYNAMIC (no caching for API) |
| Orange Cloud (proxied) | ✓ Active |

---

## Governance Alignment

From `AI_CONTEXT.md`:
```
Cloudflare (network layer)
    │
    ├── *.jesseboudreau.com → VM (reselleros tunnel)
```

BarkMind participates in this architecture correctly:
- Hostnames under `jesseboudreau.com` ✓
- Traffic via `reselleros` tunnel ✓
- No raw public port exposure (backend on 127.0.0.1) ✓
- Governance endpoints accessible via public URL ✓
