# BarkMind — Claude Code Rules

This project is governed by AI_CONTEXT.md V3 and BARKMIND_CONTEXT.md.
Read both before doing anything.

---

## Identity

BarkMind is an Aegis-governed ecosystem service.
Canonical ports: **backend 8108**, **frontend 3008**.
(Ports 8107/3007 are reserved by Aegis Lite.)
Never use any other port. Never silently fallback.

---

## Non-Negotiable Rules

- PostgreSQL only. No SQLite.
- All internal service references use `127.0.0.1`, never `localhost`.
- `NEXT_PUBLIC_*` vars never contain `127.0.0.1` or `localhost`.
- Next.js build uses `--webpack` flag.
- All AI calls route through OpenClaw at `http://127.0.0.1:18789`.
- Lifecycle scripts: `start.sh`, `stop.sh`, `restart.sh`, `status.sh` must remain functional.
- Governance endpoints (`/health`, `/whoami`, `/version`, `/.well-known/aegis-meta`) must always work.
- Port conflict detection must run in `start.sh` before launching anything.

---

## Planning Documents

All plans live in `docs/`. Read them before implementing any phase.

| File | Purpose |
|---|---|
| `docs/BUILD_PLAN.md` | Phase-by-phase build roadmap |
| `docs/AEGIS_ORCHESTRATION_PLAN.md` | Governance + Aegis integration spec |
| `docs/DATABASE_SCHEMA_PLAN.md` | PostgreSQL schema design |
| `docs/API_SURFACE_PLAN.md` | FastAPI route definitions |
| `docs/FRONTEND_ROUTE_PLAN.md` | Next.js App Router structure |
| `docs/MEDIA_PIPELINE_PLAN.md` | Upload, storage, thumbnail pipeline |
| `docs/MVP_SCOPE.md` | What is and is not in MVP |
| `docs/FUTURE_AI_ROADMAP.md` | Post-MVP AI capability roadmap |

---

## Directory Structure

```
backend/
  app/
    main.py          ← FastAPI app, governance endpoints
    config.py        ← pydantic-settings config
    database.py      ← SQLAlchemy engine
    models/          ← ORM models
    routers/         ← FastAPI routers (one file per domain)
    schemas/         ← Pydantic request/response schemas
    services/        ← Business logic (no DB queries in routers)
  requirements.txt
  alembic/           ← Alembic migration env

frontend/
  src/
    app/             ← Next.js App Router (page.tsx files)
    components/      ← Shared components
    lib/             ← API client, auth helpers, utils

config/
  apps_registry_entry.json  ← Copy into ecosystem registry

prompts/
  behavioral_summary_v1.md  ← AI prompt for case summaries

runtime/             ← PID files (gitignored)
logs/                ← Log files (gitignored)
media/               ← Local media storage (gitignored)
```

---

## What Phase We're In

Check `docs/BUILD_PLAN.md` for current phase status.
Do not skip phases. Do not implement Phase 2 before Phase 1 is done.

---

## MVP Scope Guard

Before adding any feature, check `docs/MVP_SCOPE.md`.
If it's not in the MVP scope list, it's post-MVP. Do not implement it.

---

## Aegis Registration

`start.sh` attempts registration at startup.
Registration failure is a warning, not a crash.
Aegis may be unavailable during development.
