# BarkMind — Build Plan

**Authority:** AI_CONTEXT.md V3 + BARKMIND_CONTEXT.md  
**Date:** 2026-05-17  
**Status:** Planning

---

## Identity

BarkMind is an Aegis-governed ecosystem service — not a standalone app.
It is canine behavior intelligence infrastructure.

Assigned ports:
- Backend: `8108` (8107 reserved by Aegis Lite)
- Frontend: `3008` (3007 reserved by Aegis Lite)

Hostnames:
- `barkmind-api.jesseboudreau.com` → `127.0.0.1:8108`
- `barkmind.jesseboudreau.com` → `127.0.0.1:3008`

---

## Phase Overview

| Phase | Name | Status |
|---|---|---|
| 0 | Foundation & Governance Scaffold | **COMPLETE** (2026-05-17) |
| 1 | Backend Core (FastAPI + PostgreSQL) | **COMPLETE** (2026-05-17) |
| 2 | Frontend Core (Next.js App Router) | **COMPLETE** (2026-05-17) |
| 3 | Media Pipeline | **COMPLETE** (2026-05-17) |
| 4 | Annotation Intelligence Infrastructure | **COMPLETE** (2026-05-17) |
| 5 | Expert & Reputation Systems | **COMPLETE** (2026-05-17) |
| 6 | Aegis Deep Integration | **COMPLETE** (2026-05-17) |

**Port resolution complete:** BarkMind normalized to 8108/3008. Aegis Lite retains 8107/3007.

---

## Phase 0 — Foundation & Governance Scaffold

Goal: The repo is operationally visible and governance-ready before any product logic is written.

### Deliverables

- [ ] Planning documents (this set)
- [ ] Directory structure locked
- [ ] Lifecycle scripts: `start.sh`, `stop.sh`, `restart.sh`, `status.sh`
- [ ] `.env.example` with all required vars declared
- [ ] `apps_registry.json` entry declared
- [ ] `CLAUDE.md` with project rules

### Definition of Done for Phase 0

- `start.sh` enforces port conflict detection before launching
- `status.sh` reports runtime state legibly
- All lifecycle scripts handle missing dependencies gracefully
- Cloudflare ingress entries are documented (not yet activated)

---

## Phase 1 — Backend Core

**Stack:** FastAPI + SQLAlchemy + PostgreSQL + Alembic

### Deliverables

- [ ] FastAPI application skeleton
- [ ] PostgreSQL database (`barkmind` db)
- [ ] SQLAlchemy models: User, Case, CaseMedia, Annotation, Tag, Comment
- [ ] Alembic migration chain
- [ ] Auth system: JWT-based, stateless
- [ ] Governance endpoints: `/health`, `/whoami`, `/version`, `/.well-known/aegis-meta`
- [ ] `/cases` CRUD endpoints
- [ ] `/tags` endpoint
- [ ] `/auth` endpoints (register, login, refresh)
- [ ] Aegis registration on startup

### Definition of Done for Phase 1

- All governance endpoints pass Aegis compliance check
- At least one case can be created, read, and listed via API
- Database migrations run cleanly from scratch
- Backend starts, registers with Aegis, and passes `/health`

---

## Phase 2 — Frontend Core

**Stack:** Next.js App Router, TypeScript, Tailwind CSS

### Deliverables

- [ ] Next.js project initialized with `--webpack` build
- [ ] Auth flow (login, register, token storage)
- [ ] Case browse page (`/cases`)
- [ ] Case detail page (`/cases/[id]`)
- [ ] Case submission form (`/submit`)
- [ ] Expert queue placeholder (`/expert`)
- [ ] Basic layout: header, nav, footer

### Definition of Done for Phase 2

- A user can register, log in, submit a case, and view it
- Frontend connects to backend via `NEXT_PUBLIC_API_URL`
- Build completes cleanly with `next build --webpack`

---

## Phase 3 — Media Pipeline

**Stack:** FastAPI background tasks, Pillow, ffmpeg (thumbnails), local disk → S3-ready

### Deliverables

- [ ] Image upload endpoint with MIME validation
- [ ] Video upload endpoint with size cap
- [ ] Thumbnail generation (images: Pillow, video: ffmpeg frame extract)
- [ ] Structured storage directory with retention logic
- [ ] Media served via FastAPI static or redirect

### Definition of Done for Phase 3

- Image and video uploads work end-to-end
- Thumbnails generated automatically
- Storage path is configurable via env var (local for MVP, S3 URI in future)

---

## Phase 4 — AI Integration

**Stack:** Claude API via OpenClaw gateway (`http://127.0.0.1:18789`)

### Deliverables

- [ ] POST `/cases/{id}/summarize` → structured AI behavioral summary
- [ ] AI summary stored as a structured field on Case
- [ ] Prompt library in `/prompts/`
- [ ] OpenClaw routing configured

### Definition of Done for Phase 4

- A case with annotations can be summarized by AI
- AI summary is persisted and displayed on case detail page
- Prompt is versioned

---

## Phase 5 — Expert & Reputation Systems

### Deliverables

- [ ] Expert role on User model
- [ ] POST `/cases/{id}/resolve` → expert resolution record
- [ ] Resolution rendered on case detail page
- [ ] Basic contributor reputation model (case count, resolution count)

### Definition of Done for Phase 5

- Experts can mark a case resolved with a structured judgment
- Non-experts cannot resolve cases (role enforcement)

---

## Phase 6 — Aegis Deep Integration

### Deliverables

- [ ] Startup registration via Aegis registry API
- [ ] Topology drift detection
- [ ] Compliance score visible in Aegis dashboard
- [ ] Runtime metadata streamed to Aegis

### Definition of Done for Phase 6

- BarkMind appears in Aegis topology view
- Compliance score is non-zero and accurate
- Aegis can restart/stop BarkMind via lifecycle hooks

---

## Constraints

- PostgreSQL only — no SQLite, no in-memory DB
- Ports 8107/3007 — no fallback, no silent conflict
- `127.0.0.1` for all internal service references
- Next.js uses `--webpack` build flag
- Docker-ready from day one (env var config, graceful SIGTERM, stdout logging)
- No fake AI complexity, no premature agents, no bloated microservices
