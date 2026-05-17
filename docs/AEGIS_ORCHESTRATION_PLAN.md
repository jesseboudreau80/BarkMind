# BarkMind — Aegis Orchestration Plan

**Authority:** AI_CONTEXT.md V3 Section 3, 4, 5  
**Date:** 2026-05-17

---

## Role

BarkMind is a topology participant, not an independent app.
Aegis is its governance authority.

---

## Assigned Identity

```
app_id:        barkmind
backend_port:  8107
frontend_port: 3007
backend_host:  barkmind-api.jesseboudreau.com
frontend_host: barkmind.jesseboudreau.com
owner:         jesse
```

---

## Required Governance Endpoints

All endpoints are implemented on the FastAPI backend (port 8107).

### GET /health

```json
{
  "status": "ok",
  "service": "barkmind",
  "version": "1.0.0"
}
```

Used by: Aegis health polling, uptime monitoring, load balancer checks.

### GET /whoami

```json
{
  "app": "barkmind",
  "version": "1.0.0",
  "port": 8107,
  "environment": "local",
  "owner": "jesse",
  "aegis_connected": true
}
```

Used by: Aegis runtime identity verification, topology audit.

### GET /.well-known/aegis-meta

```json
{
  "app": "barkmind",
  "description": "Canine behavior intelligence platform",
  "version": "1.0.0",
  "owner": "jesse",
  "doctrine_version": "2026-05-10",
  "runtime_mode": "production",
  "deployment_env": "local",
  "backend_port": 8107,
  "frontend_port": 3007,
  "lifecycle_support": true,
  "topology_registered": true
}
```

Used by: Aegis compliance scoring, topology reconciliation.

### GET /version

```json
{
  "version": "1.0.0",
  "commit": "{{GIT_COMMIT}}",
  "built_at": "{{BUILD_TIMESTAMP}}"
}
```

---

## Startup Registration Flow

On every startup, BarkMind must:

1. Check that port 8107 is not occupied (`lsof -ti:8107`)
   - If occupied: print error, exit non-zero, do NOT start
2. Verify `.env` is present and contains required vars
3. Start FastAPI process
4. POST registration payload to Aegis:

```
POST http://127.0.0.1:8102/api/apps/register
X-User-Email: admin@dpvet.com
Content-Type: application/json

{
  "app_id": "barkmind",
  "name": "BarkMind",
  "backend_port": 8107,
  "frontend_port": 3007,
  "backend_url": "http://127.0.0.1:8107",
  "frontend_url": "http://127.0.0.1:3007",
  "health_endpoint": "http://127.0.0.1:8107/health",
  "meta_endpoint": "http://127.0.0.1:8107/.well-known/aegis-meta",
  "lifecycle": ["start", "stop", "restart", "status"]
}
```

5. Log registration result (success or failure — do not crash on Aegis unavailability)

**Note:** Registration failure should be logged with a warning but must not prevent BarkMind startup.
Aegis may be unavailable during development. BarkMind's governance responsibility is to attempt
registration and remain discoverable.

---

## Port Conflict Enforcement

Implemented in `start.sh`:

```bash
if lsof -ti:8107 &>/dev/null; then
  echo "[BARKMIND] ERROR: Port 8107 is already in use. Refusing to start."
  echo "[BARKMIND] Run: lsof -ti:8107 | xargs ps -p to identify occupant."
  exit 1
fi
```

Same check for port 3007 (frontend).

---

## Topology Declaration (apps_registry.json)

BarkMind must be declared in the ecosystem registry:

```json
{
  "app_id": "barkmind",
  "name": "BarkMind",
  "description": "Canine behavior intelligence platform",
  "backend_port": 8107,
  "frontend_port": 3007,
  "backend_host": "barkmind-api.jesseboudreau.com",
  "frontend_host": "barkmind.jesseboudreau.com",
  "owner": "jesse",
  "status": "active",
  "lifecycle_scripts": true,
  "health_check": "/health",
  "meta_endpoint": "/.well-known/aegis-meta",
  "docker_ready": false,
  "notes": "Canine behavior review, annotation, and AI-assisted intelligence platform"
}
```

---

## Cloudflare Ingress Declaration

To be added to `~/.cloudflared/config.yml` (reselleros tunnel):

```yaml
# BarkMind
- hostname: barkmind-api.jesseboudreau.com
  service: http://127.0.0.1:8107

- hostname: barkmind.jesseboudreau.com
  service: http://127.0.0.1:3007
```

**Rules:**
- Add before the terminal `http_status:404` catch-all
- Never duplicate these hostnames
- Never use quick tunnels

---

## OpenClaw Integration (Phase 4)

BarkMind will route AI calls through OpenClaw:

```
AI Summary request → http://127.0.0.1:18789/v1/chat/completions
```

Configuration:
```
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_MODEL=claude-sonnet-4-6
```

OpenClaw handles:
- Model routing
- Rate limiting
- Audit logging
- Token accounting

BarkMind does NOT call Anthropic API directly.

---

## Future Aegis Orchestration Hooks

When Aegis gains lifecycle orchestration capability:

| Aegis Command | BarkMind Response |
|---|---|
| `aegis restart barkmind` | Executes `restart.sh` |
| `aegis stop barkmind` | Executes `stop.sh` |
| `aegis health barkmind` | Returns `/health` JSON |
| `aegis status barkmind` | Returns runtime state |

BarkMind lifecycle scripts must be idempotent and safe to call remotely.

---

## Compliance Checklist

| Requirement | Implementation |
|---|---|
| Port governance | `start.sh` exits on port conflict |
| Canonical ports | 8107 / 3007 hardcoded |
| 127.0.0.1 only | All internal refs use 127.0.0.1 |
| Metadata endpoints | /health, /whoami, /.well-known/aegis-meta, /version |
| Lifecycle scripts | start, stop, restart, status |
| Registry declaration | apps_registry.json entry |
| Tunnel declaration | cloudflared config entries |
| OpenClaw routing | AI calls go through 127.0.0.1:18789 |
| Docker readiness | env var config, graceful SIGTERM, stdout logging |
