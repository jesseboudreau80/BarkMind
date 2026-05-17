# BarkMind — Aegis Integration

**Date:** 2026-05-17  
**Phase:** 6 Complete

---

## Integration Points

BarkMind connects to Aegis through:

### 1. Startup Registration

On every startup, `main.py` POSTs to Aegis:

```
POST http://127.0.0.1:8102/api/apps/register
X-User-Email: admin@dpvet.com
{
  "app_id": "barkmind",
  "backend_port": 8107,
  "frontend_port": 3007,
  "health_endpoint": "http://127.0.0.1:8107/health",
  "meta_endpoint": "http://127.0.0.1:8107/.well-known/aegis-meta",
  "lifecycle": ["start", "stop", "restart", "status"]
}
```

Registration failure is a warning, not a crash. Aegis may be offline during development.

### 2. Governance Endpoints (Aegis Polling)

These endpoints respond without JWT auth — Aegis can poll them directly:

| Endpoint | What Aegis Gets |
|---|---|
| `GET /health` | `{status, service, version}` |
| `GET /whoami` | Runtime identity |
| `GET /version` | `{version, commit, built_at}` |
| `GET /.well-known/aegis-meta` | Full capability declaration |
| `GET /governance/status` | Live governance metrics + capabilities |
| `GET /governance/metrics` | Quantitative platform metrics |

### 3. Service-to-Service Auth

For endpoints that require auth but are polled by Aegis:

```
X-Service-Key: <SERVICE_API_KEY>
```

Set `SERVICE_API_KEY` in `.env`. Currently used by `/telemetry/events`.

### 4. Manifest Files

**`config/aegis.manifest.json`** — static declaration read by Aegis registry  
**`config/aegis.runtime.yml`** — runtime capability declaration for Aegis compliance scoring

---

## Aegis Compliance Checklist

| Requirement | Status |
|---|---|
| Port conflict detection (start.sh) | ✓ |
| Canonical ports (8107/3007) | ✓ |
| 127.0.0.1 for all internal refs | ✓ |
| /health endpoint | ✓ |
| /whoami endpoint | ✓ |
| /version endpoint | ✓ |
| /.well-known/aegis-meta | ✓ |
| Lifecycle scripts (start/stop/restart/status) | ✓ |
| Registry declaration (apps_registry_entry.json) | ✓ |
| Tunnel declaration (cloudflared) | documented |
| Aegis startup registration | ✓ |
| Governance status endpoint | ✓ Phase 6 |
| Governance metrics endpoint | ✓ Phase 6 |
| Telemetry events endpoint | ✓ Phase 6 |
| Capability declarations | ✓ Phase 6 |
| Docker readiness | config-ready (not packaged) |

---

## OpenClaw Integration

All AI calls route through OpenClaw:

```
OPENCLAW_BASE_URL=http://127.0.0.1:18789
OPENCLAW_MODEL=claude-sonnet-4-6
```

BarkMind never calls Anthropic API directly.
OpenClaw handles: model routing, rate limiting, audit logging, token accounting.

---

## Future Aegis Orchestration

When Aegis gains full lifecycle orchestration:

| Aegis Command | BarkMind Action |
|---|---|
| `aegis restart barkmind` | Executes `./restart.sh` |
| `aegis stop barkmind` | Executes `./stop.sh` |
| `aegis health barkmind` | Polls `/health` |
| `aegis governance barkmind` | Polls `/governance/status` |
| `aegis metrics barkmind` | Polls `/governance/metrics` |
| `aegis events barkmind` | Polls `/telemetry/events` |

Lifecycle scripts are idempotent and safe to call remotely.
