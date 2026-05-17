# BarkMind — API Surface Plan

**Stack:** FastAPI  
**Base URL:** `https://barkmind-api.jesseboudreau.com`  
**Internal:** `http://127.0.0.1:8107`  
**Date:** 2026-05-17

---

## Design Principles

- REST-first, no GraphQL complexity for MVP
- JSON request/response bodies
- JWT Bearer auth on all protected routes
- Role enforcement at the route level (`user`, `expert`, `admin`)
- Consistent error envelope: `{ "detail": "...", "code": "..." }`
- Pagination: cursor-based on list endpoints (`?cursor=&limit=`)
- Versioned by path prefix when breaking changes are needed (`/v1/` reserved, not used in MVP)

---

## Auth Convention

```
Authorization: Bearer <jwt_token>
```

Token payload:
```json
{
  "sub": "<user_id>",
  "role": "user",
  "exp": <unix_timestamp>
}
```

---

## Governance Endpoints (No Auth Required)

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check — Aegis health polling |
| GET | `/whoami` | Runtime identity metadata |
| GET | `/version` | Git commit + version string |
| GET | `/.well-known/aegis-meta` | Full Aegis compliance metadata |

These four endpoints must respond even when the database is unreachable.

---

## Auth Routes — `/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | None | Create account |
| POST | `/auth/login` | None | Returns JWT access + refresh token |
| POST | `/auth/refresh` | Refresh token | Rotate access token |
| POST | `/auth/logout` | Bearer | Invalidate refresh token |

### POST /auth/register

```json
Request:  { "email": "", "username": "", "password": "", "display_name": "" }
Response: { "user_id": "", "username": "", "access_token": "", "refresh_token": "" }
```

### POST /auth/login

```json
Request:  { "email": "", "password": "" }
Response: { "access_token": "", "refresh_token": "", "user": { "id": "", "username": "", "role": "" } }
```

---

## Cases — `/cases`

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/cases` | Optional | — | Browse cases (public feed) |
| POST | `/cases` | Required | user+ | Submit a new case |
| GET | `/cases/{id}` | Optional | — | Get case detail |
| PATCH | `/cases/{id}` | Required | submitter or admin | Update case metadata |
| DELETE | `/cases/{id}` | Required | submitter or admin | Archive case |
| POST | `/cases/{id}/summarize` | Required | expert or admin | Trigger AI summary |

### GET /cases — Query Params

```
?status=open|under_review|resolved
?tag=<slug>
?setting=<setting>
?search=<text>
?cursor=<cursor>
?limit=20 (default, max 100)
```

### POST /cases

```json
Request: {
  "title": "",
  "description": "",
  "setting": "daycare|shelter|home|grooming|vet|other",
  "subject_age_estimate": "puppy|adult|senior",
  "subject_breed_note": "",
  "trigger_context": ""
}
Response: { "id": "", "status": "open", "created_at": "" }
```

### GET /cases/{id}

```json
Response: {
  "id": "", "title": "", "description": "", "status": "",
  "setting": "", "submitter": { "username": "", "reputation_score": 0 },
  "tags": [...],
  "annotations": [...],
  "media": [...],
  "comments_count": 0,
  "expert_resolution": null,
  "ai_summary": null,
  "created_at": ""
}
```

---

## Case Media — `/cases/{id}/media`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/cases/{id}/media` | Required | Upload image or video |
| GET | `/cases/{id}/media` | Optional | List media for case |
| DELETE | `/cases/{id}/media/{media_id}` | Required | Remove media (owner/admin) |

### POST /cases/{id}/media

- Content-Type: `multipart/form-data`
- Field: `file`
- Accepted MIME: `image/jpeg`, `image/png`, `image/webp`, `video/mp4`, `video/quicktime`
- Max size: images 20 MB, videos 500 MB

```json
Response: {
  "id": "",
  "media_type": "image|video",
  "thumbnail_url": "",
  "processing_status": "pending",
  "created_at": ""
}
```

---

## Tags — `/tags`

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/tags` | Optional | — | List all tags (grouped by category) |
| GET | `/tags/{slug}` | Optional | — | Get single tag detail |
| POST | `/tags` | Required | admin | Create tag |

### GET /tags Response

```json
{
  "categories": {
    "body_language": [ { "slug": "", "label": "", "severity_hint": 0 } ],
    "vocalization": [...],
    "posture": [...],
    "interaction": [...],
    "context": [...]
  }
}
```

---

## Case Tags — `/cases/{id}/tags`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/cases/{id}/tags` | Optional | Get tags on a case |
| POST | `/cases/{id}/tags` | Required | Apply a tag to a case |
| DELETE | `/cases/{id}/tags/{tag_id}` | Required | Remove tag (applier or admin) |

### POST /cases/{id}/tags

```json
Request: {
  "tag_slug": "",
  "confidence": "observed|probable|possible",
  "timestamp_note": ""
}
```

---

## Annotations — `/cases/{id}/annotations`

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/cases/{id}/annotations` | Optional | — | List annotations |
| POST | `/cases/{id}/annotations` | Required | user+ | Add annotation |
| PATCH | `/cases/{id}/annotations/{ann_id}` | Required | author or admin | Edit annotation |
| DELETE | `/cases/{id}/annotations/{ann_id}` | Required | author or admin | Remove annotation |

### POST /cases/{id}/annotations

```json
Request: {
  "annotation_type": "observation|interpretation|concern|recommendation",
  "body": "",
  "media_id": null,
  "timestamp_start": null,
  "timestamp_end": null,
  "metadata": {}
}
```

---

## Comments — `/cases/{id}/comments`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/cases/{id}/comments` | Optional | Threaded comment list |
| POST | `/cases/{id}/comments` | Required | Add comment |
| PATCH | `/cases/{id}/comments/{comment_id}` | Required | Edit (author only) |
| DELETE | `/cases/{id}/comments/{comment_id}` | Required | Archive (author or admin) |

### POST /cases/{id}/comments

```json
Request: { "body": "", "parent_id": null }
```

---

## Expert Resolutions — `/cases/{id}/resolution`

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/cases/{id}/resolution` | Optional | — | Get resolution if exists |
| POST | `/cases/{id}/resolution` | Required | expert, admin | Submit resolution |
| PATCH | `/cases/{id}/resolution` | Required | expert, admin | Update resolution |

### POST /cases/{id}/resolution

```json
Request: {
  "verdict": "safe|concern|escalation_risk|requires_intervention",
  "summary": "",
  "recommendations": "",
  "confidence_level": "high|medium|low"
}
```

On submission: case status is updated to `resolved`.

---

## AI — `/cases/{id}/summarize`

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| POST | `/cases/{id}/summarize` | Required | expert, admin | Trigger AI behavioral summary |

Calls OpenClaw at `http://127.0.0.1:18789`.
Stores result in `cases.ai_summary`.
Returns summary immediately (synchronous for MVP).

```json
Response: {
  "summary": "",
  "prompt_version": "v1",
  "generated_at": ""
}
```

---

## Users — `/users`

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/users/me` | Required | Get own profile |
| PATCH | `/users/me` | Required | Update display_name, bio |
| GET | `/users/{username}` | Optional | Public profile + case history |

---

## Admin — `/admin`

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | `/admin/users` | Required | admin | List users |
| PATCH | `/admin/users/{id}/role` | Required | admin | Change user role |
| GET | `/admin/cases` | Required | admin | All cases including archived |
| DELETE | `/admin/cases/{id}` | Required | admin | Hard delete (rare) |

---

## Error Envelope

All errors return:

```json
{
  "detail": "Human-readable error message",
  "code": "machine_readable_code"
}
```

Common codes:
- `not_found`
- `unauthorized`
- `forbidden`
- `validation_error`
- `port_conflict`
- `media_too_large`
- `unsupported_mime`

---

## OpenAPI

FastAPI auto-generates OpenAPI at:
- `http://127.0.0.1:8107/docs` (Swagger UI)
- `http://127.0.0.1:8107/openapi.json`
