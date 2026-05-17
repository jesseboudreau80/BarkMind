# BarkMind — Known Limitations

**Date:** 2026-05-17  
**Status:** MVP — all limitations documented, none blocking core functionality

---

## Infrastructure

### 1. Aegis Registration Returns 404

**Status:** Non-blocking warning  
**Description:** The Aegis registration POST to `/api/apps/register` returns 404, suggesting the Aegis API path may differ from what BarkMind expects.  
**Impact:** BarkMind logs a warning at startup but runs normally. Aegis topology shows BarkMind as unregistered.  
**Mitigation:** BarkMind exposes all required governance endpoints (`/health`, `/governance/status`, `/.well-known/aegis-meta`) for manual registration or polling.  
**Resolution:** Verify correct Aegis registration endpoint path and update `_register_with_aegis()` in `main.py`.

### 2. Cloudflare Tunnel Not Configured

**Status:** Deployment step pending  
**Description:** `barkmind-api.jesseboudreau.com` and `barkmind.jesseboudreau.com` are not yet in the cloudflared tunnel config.  
**Impact:** Platform accessible only on `127.0.0.1` — not via public hostnames.  
**Resolution:** Add to `~/.cloudflared/config.yml` per docs/AEGIS_ORCHESTRATION_PLAN.md.

### 3. No Process Supervisor

**Status:** Acceptable for MVP  
**Description:** Backend and frontend are started with `setsid disown` — they survive terminal closure but have no automatic restart on crash.  
**Impact:** A backend crash requires manual `./restart.sh`.  
**Resolution (post-MVP):** Add `systemd` service units or `supervisor` configuration.

---

## Feature Limitations

### 4. Password Reset Not Implemented

**Status:** MVP deferral (documented in MVP_SCOPE.md)  
**Description:** Forgotten passwords require admin DB intervention.  
**Workaround:** Admin runs: `UPDATE users SET password_hash='...' WHERE username='...'`

### 5. Video Thumbnail Seeks at 2s (Short Videos May Miss)

**Status:** Minor edge case  
**Description:** `generate_video_thumbnails()` tries frame at 2s, 1s, 0.5s, 0s. Very short videos (< 0.5s) produce a seek-0 frame which may be blank.  
**Impact:** Thumbnails may be blank/dark for very short clips.  
**Workaround:** None — ffmpeg returns whatever frame exists at 0s.

### 6. Export Jobs Are Synchronous

**Status:** Acceptable for MVP (small dataset)  
**Description:** Export endpoints generate the full dataset in-request. For large datasets this blocks the request for multiple seconds.  
**Impact:** Admin export of large datasets may timeout at gateway level.  
**Resolution (post-MVP):** Move export to background job + download URL pattern.

### 7. Annotation `extra_data` JSONB Mutation Requires `flag_modified`

**Status:** Handled (known pattern)  
**Description:** SQLAlchemy does not detect in-place dict mutations on JSONB columns. Code must call `flag_modified(record, "thumbnails")` after assigning a new dict.  
**Impact:** If a developer adds JSONB column updates without `flag_modified`, the change may not persist.  
**Mitigation:** Pattern is documented in `CLAUDE.md`.

### 8. Consensus Minimum Opinion Count Not Enforced

**Status:** By design (configurable in future)  
**Description:** A consensus record with a single expert opinion is technically "reached" (100% = high confidence). Operationally, a consensus of 1 is not meaningful.  
**Impact:** Admins initiating consensus must manually ensure multiple experts submit opinions before considering it valid.  
**Resolution (post-MVP):** Add `min_opinions` field to `ConsensusRecord` and enforce in vote counting.

---

## Multi-Tenant

### 9. Organization Isolation Not Enforced

**Status:** Foundation only (Phase 6 architecture)  
**Description:** `users.organization_id` FK exists, but no query filtering by `organization_id` is implemented.  
**Impact:** All users can see all cases, annotations, and experts regardless of organization.  
**Resolution (post-MVP):** Add `WHERE organization_id = $org` to relevant queries.

---

## Performance

### 10. Analytics Computed On Demand

**Status:** Acceptable for current data volume  
**Description:** All analytics endpoints run live SQL aggregations on every request. No caching.  
**Impact:** On large datasets (10k+ cases), analytics queries may be slow.  
**Resolution (post-MVP):** Add Redis cache with 60s TTL on `/governance/metrics` and `/analytics/*`.

### 11. Event Stream Has No Cursor Persistence

**Status:** Minor  
**Description:** Event replay via `?since=` works, but there is no server-side cursor management. Clients must track their own last-seen timestamp.  
**Impact:** If a consumer crashes without saving its position, it may replay events.  
**Resolution (post-MVP):** Add consumer cursor tracking table.
