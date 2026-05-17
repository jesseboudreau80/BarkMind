# BarkMind — MVP Scope

**Date:** 2026-05-17  
**Status:** Authoritative definition of MVP

---

## What Is the MVP

The MVP is a working canine behavior review platform where:

1. A user can submit a behavior case with media
2. The community can annotate and tag the case
3. An expert can resolve the case with a structured verdict
4. An AI summary can be generated on demand
5. Cases are searchable and browsable

That's it. Everything else is future scope.

---

## MVP Is

### Users
- Registration and login (email + password)
- Three roles: `user`, `expert`, `admin`
- Public profile page (username, bio, case count)

### Cases
- Submit a behavior review case
- Fields: title, description, setting, subject age estimate, breed note, trigger context
- Case statuses: `open`, `under_review`, `resolved`, `archived`
- Browse and search cases
- Case detail page with all associated data

### Media
- Upload images (JPEG, PNG, WebP) and videos (MP4, MOV)
- Automatic thumbnail generation
- Images: up to 20 MB
- Videos: up to 500 MB
- One or more media items per case

### Behavioral Tags
- Curated tag vocabulary (seeded, ~25 tags)
- Tags grouped by category: body language, vocalization, posture, interaction, context
- Apply tags to cases with confidence level (`observed`, `probable`, `possible`)
- Optional timestamp note for video references
- Remove own tags

### Annotations
- Add structured observations to a case
- Four types: `observation`, `interpretation`, `concern`, `recommendation`
- Optional: link to specific media, specify timestamp range
- Expert annotations visually distinguished

### Comments
- Community comments on a case
- One level of threading (replies to comments)

### Expert Resolutions
- Experts can submit a formal verdict on a case
- Verdict options: `safe`, `concern`, `escalation_risk`, `requires_intervention`
- Includes: written summary, recommendations, confidence level
- Case status transitions to `resolved`

### AI Summary
- Experts or admins can trigger an AI behavioral summary
- Summary generated from case description + annotations + tags
- Stored and displayed on case detail page
- Prompt versioned
- Routes through OpenClaw gateway

### Governance
- `/health`, `/whoami`, `/version`, `/.well-known/aegis-meta` endpoints
- Startup registration with Aegis
- Port conflict detection on startup
- Lifecycle scripts: start, stop, restart, status

---

## MVP Is NOT

The following are explicitly deferred. Do not implement them in MVP.

### Features Not In MVP
- Real-time notifications (WebSocket, SSE)
- Reputation scoring and leaderboards
- Video frame analysis or per-frame annotation
- Multimodal AI analysis (sending video frames to AI)
- Behavioral risk scoring or escalation prediction
- Daycare grouping recommendations
- Veterinary restraint guidance
- Shelter intake workflows
- Training dataset exports
- API key access for external researchers
- Public API / third-party integrations
- Social features (follow users, case bookmarks, likes)
- Email notifications
- Password reset flow (admin can reset manually for MVP)
- OAuth (Google/GitHub login)
- Annotation upvoting / community consensus scoring
- Tag suggestions from AI
- Any mobile app or native client
- Docker packaging (Docker-ready in config, not packaged)
- Kubernetes deployment
- Multi-tenancy or organization accounts
- Advanced search (Elasticsearch, vector similarity)
- Behavioral trend analytics dashboards

---

## MVP Quality Bar

An MVP session is complete when:

- [ ] A fresh user can register, submit a case with media, and tag it
- [ ] An expert can log in, add annotations, and submit a resolution
- [ ] An admin can trigger an AI summary
- [ ] All governance endpoints respond correctly
- [ ] `start.sh` enforces port conflict detection
- [ ] `status.sh` shows whether processes are running
- [ ] Database migrations run from scratch without error
- [ ] Frontend builds with `next build --webpack` without error
- [ ] BarkMind appears in Aegis topology (or registration is attempted with warning on failure)

---

## Scope Guard

Before adding any feature during MVP build, ask:
1. Is this required for a user to submit and review a behavior case?
2. Is this required for an expert to resolve a case?
3. Is this required for Aegis governance compliance?

If the answer to all three is no, it is post-MVP.
