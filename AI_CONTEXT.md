# AI Context V3 — Ecosystem Build Doctrine
## Jesse Boudreau Stack — Aegis-Native Edition

**Supersedes:** AI_CONTEXT.md (V2)  
**Date:** 2026-05-10  
**Authority:** This document governs all Claude Code builds in the Jesse Boudreau ecosystem.

---

## CORE IDENTITY SHIFT

Apps in this ecosystem are **NOT standalone experiments**.

They are:
- Ecosystem services running under Aegis governance
- Operationally visible runtimes tracked by the control plane
- Governance-aware systems that expose their state
- Future Docker-ready services following standard patterns

Claude must build with this identity in mind at all times.

---

## SECTION 1 — Ecosystem Architecture

### The Stack

\`\`\`
Cloudflare (network layer)
    │
    ├── *.jesseboudreau.com → VM (reselleros tunnel)
    │
VM: vmi3002990
    │
    ├── Aegis AI (governance platform) @ :8102 / :3002
    ├── DevOS (builder) @ :8104 / :3004
    ├── n8n (automation) @ :5678
    ├── OpenClaw (AI gateway) @ :18789
    ├── ResellerOS @ :8101 / :3001
    ├── Guilded @ :8100 / :3000
    ├── DP-DVM-Map @ :8103 / :3003
    ├── PackGuardian @ :8105 / :3005
    ├── jesseboudreau.com @ :3006
    └── [Your New App] @ [canonical assigned ports]
\`\`\`

### Role of Each System

| System | Role |
|---|---|
| **Aegis AI** | Governance platform, operational control plane |
| **DevOS** | App builder, scaffolding, deployment engine |
| **Cloudflare** | Network layer, tunnel routing |
| **Supabase** | Persistent state for Aegis |
| **n8n** | Workflow automation |
| **Your App** | Ecosystem service, governed by Aegis |

### How New Apps Fit

Every new app is an **Aegis-governed ecosystem service**. It must:
1. Expose governance-compatible endpoints
2. Register with Aegis at startup
3. Follow canonical port/tunnel/logging standards
4. Include operational lifecycle scripts
5. Publish runtime metadata
6. Participate in topology governance

---

## SECTION 2 — Infrastructure Governance Doctrine

### Canonical Permanent Ports

| App | Frontend | Backend |
|---|---|---|
| Guilded | 3000 | 8100 |
| ResellerOS | 3001 | 8101 |
| Aegis | 3002 | 8102 |
| DP-DVM-Map | 3003 | 8103 |
| DevOS | 3004 | 8104 |
| PackGuardian | 3005 | 8105 |
| jesseboudreau.com | 3006 | 8106 |

### Critical Rules

\`\`\`
✅ ALWAYS use 127.0.0.1 internally
❌ NEVER use localhost for backend service references

✅ ALWAYS use canonical assigned ports
❌ NEVER arbitrarily assign ports

✅ ALWAYS register apps in apps_registry.json
❌ NEVER run unmanaged services outside governance

✅ ALWAYS expose metadata endpoints
❌ NEVER run opaque runtimes
\`\`\`

### Port Governance

Before startup:

\`\`\`bash
curl -s http://127.0.0.1:8102/infrastructure/ports \
  -H "X-User-Email: admin@dpvet.com"
\`\`\`

If occupied:
- FAIL startup immediately
- NEVER share ports
- NEVER silently fallback

### Tunnel Governance

Canonical tunnel:

\`\`\`
reselleros
\`\`\`

Rules:
- one tunnel
- one authoritative config
- one ingress authority
- no duplicate hostname mappings
- no quick tunnels

---

## SECTION 3 — Required Runtime Endpoints

Every governed app MUST expose:

### GET /health

\`\`\`json
{
  "status": "ok",
  "service": "my-app",
  "version": "1.0.0"
}
\`\`\`

### GET /whoami

\`\`\`json
{
  "app": "my-app",
  "version": "1.0.0",
  "port": 8102,
  "environment": "local",
  "owner": "jesse",
  "aegis_connected": true
}
\`\`\`

### GET /.well-known/aegis-meta

\`\`\`json
{
  "app": "my-app",
  "description": "What this app does",
  "version": "1.0.0",
  "owner": "jesse",
  "doctrine_version": "2026-05-10",
  "runtime_mode": "production",
  "deployment_env": "local",
  "backend_port": 8102,
  "frontend_port": 3000,
  "lifecycle_support": true,
  "topology_registered": true
}
\`\`\`

### GET /version

\`\`\`json
{
  "version": "1.0.0",
  "commit": "abc1234",
  "built_at": "2026-05-10T..."
}
\`\`\`

---

## SECTION 4 — Required Lifecycle Scripts

Every governed app MUST include:

\`\`\`
start.sh
stop.sh
restart.sh
status.sh
\`\`\`

### Startup Governance Enforcement

Apps MUST refuse startup if:
- canonical port occupied
- registry mismatch exists
- tunnel mismatch exists
- metadata endpoint missing
- runtime identity invalid

### Required Startup Pattern

\`\`\`bash
setsid ... &
disown
trap cleanup INT TERM
# NEVER trap EXIT
\`\`\`

---

## SECTION 5 — Registry & Topology Governance

### apps_registry.json

This file is the:
- topology authority
- ingress authority
- port authority
- runtime authority
- ecosystem inventory

No app exists outside the registry.

### Aegis Governance Responsibilities

Aegis is now:
- topology authority
- runtime authority
- ingress authority
- governance authority
- reconciliation engine
- ecosystem registry authority

### Topology Governance Features

Aegis validates:
- port ownership
- tunnel ownership
- runtime identity
- metadata compliance
- lifecycle support
- orphan runtimes
- stale services
- topology drift

### Compliance Scoring

Every app receives:
- infrastructure compliance score
- governance compliance score
- topology reconciliation status

---

## SECTION 6 — Cloudflare Standard

### Config Location

\`\`\`
~/.cloudflared/config.yml
\`\`\`

### Canonical Ingress Pattern

\`\`\`yaml
ingress:
  - hostname: my-app-api.jesseboudreau.com
    service: http://127.0.0.1:8102

  - hostname: my-app.jesseboudreau.com
    service: http://127.0.0.1:3000

  - service: http_status:404
\`\`\`

### Important

\`\`\`
❌ NEVER duplicate hostnames
❌ NEVER use quick tunnels
❌ NEVER mix localhost + 127.0.0.1
\`\`\`

---

## SECTION 7 — Database Doctrine

\`\`\`
✅ ALWAYS PostgreSQL
✅ Separate DB per app
✅ SQLAlchemy ORM
✅ JSONB allowed
❌ NEVER SQLite
❌ NEVER in-memory production DBs
\`\`\`

---

## SECTION 8 — Frontend Standard

### Framework

\`\`\`
Next.js App Router
\`\`\`

### Build Stability

\`\`\`json
"build": "next build --webpack"
\`\`\`

Required because:
- Turbopack causes intermittent ENOENT race failures on VM builds

### API URLs

\`\`\`
NEXT_PUBLIC_API_URL=https://my-app-api.jesseboudreau.com
\`\`\`

Never:
- localhost
- 127.0.0.1
- internal IPs
inside NEXT_PUBLIC vars

---

## SECTION 9 — Dockerization Doctrine

Apps must be Docker-ready from day one.

### Requirements

\`\`\`
✅ Config via env vars
✅ Graceful SIGTERM handling
✅ Explicit port binding
✅ Stateless runtime
✅ stdout/stderr logging
\`\`\`

### Future Architecture

Aegis will eventually:
- generate Docker configs
- generate Compose files
- validate deployments
- orchestrate runtime lifecycle
- monitor containers
- govern topology automatically

---

## SECTION 10 — Build Philosophy

Apps are NOT demos.

Apps are:
- governed ecosystem services
- operational runtimes
- topology participants
- infrastructure citizens

### Definition of Done

An app is only complete when:
- startup lifecycle works
- topology registration works
- Cloudflare routing works
- metadata endpoints work
- health checks pass
- governance reconciliation passes
- Aegis visibility exists
- runtime is operationally manageable

### Core Philosophy

\`\`\`
Port conflicts are bugs.
Silent failures are bugs.
Opaque runtimes are bugs.
Infrastructure ambiguity is a bug.
\`\`\`

---

## SECTION 11 — Future Direction

The ecosystem is evolving toward:
- autonomous DevOS
- AI-native infrastructure governance
- self-healing topology
- runtime orchestration
- governed AI workforce systems
- Docker/Kubernetes deployment orchestration
- enterprise governance visibility

Aegis is becoming:
- governance OS
- infrastructure control plane
- runtime authority
- operational visibility layer

---

*"Automation must remain accountable."*
