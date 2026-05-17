# BarkMind — API Testing Guide

**Base URL (production):** `https://barkmind-api.jesseboudreau.com`  
**Base URL (local):** `http://127.0.0.1:8107`

---

## Prerequisites

- Backend running: `./start.sh` (or `uvicorn app.main:app --host 127.0.0.1 --port 8107` from `backend/`)
- PostgreSQL running with `barkmind` database

---

## Quick Environment Setup

```bash
export BASE=http://127.0.0.1:8107

# Register a test user
curl -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@example.com","username":"tester1","password":"password123"}'

# Login and capture token
TOKEN=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@example.com","password":"password123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo "Token captured: ${TOKEN:0:30}..."
```

---

## Governance Endpoints

```bash
# Health check
curl $BASE/health

# Runtime identity
curl $BASE/whoami

# Aegis compliance metadata
curl $BASE/.well-known/aegis-meta

# Version + git commit
curl $BASE/version
```

---

## Auth

### Register
```bash
curl -X POST $BASE/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "myusername",
    "password": "password123",
    "display_name": "My Name"
  }'
```

### Login
```bash
curl -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### Get Current User
```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/auth/me
```

### Refresh Token
```bash
curl -X POST $BASE/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<your_refresh_token>"}'
```

---

## Cases

### Create Case
```bash
CASE=$(curl -s -X POST $BASE/cases \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Lab mix freezing during group play",
    "description": "Subject showed freeze behavior during morning daycare session.",
    "setting": "daycare",
    "subject_age_estimate": "adult",
    "subject_breed_note": "Black lab mix, 4 years",
    "trigger_context": "Resource competition over ball"
  }')

CASE_ID=$(echo $CASE | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo "Case ID: $CASE_ID"
```

### List Cases (with filters)
```bash
# All open cases
curl "$BASE/cases?status=open"

# Filter by tag
curl "$BASE/cases?tag=freeze"

# Filter by setting
curl "$BASE/cases?setting=daycare"

# Search
curl "$BASE/cases?search=piloerection"

# Pagination
curl "$BASE/cases?limit=10"
curl "$BASE/cases?cursor=2026-05-17T12:00:00Z&limit=10"
```

### Get Case Detail
```bash
curl $BASE/cases/$CASE_ID
```

### Update Case
```bash
curl -X PATCH $BASE/cases/$CASE_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"description": "Updated description with more context."}'
```

### Archive Case
```bash
curl -X DELETE $BASE/cases/$CASE_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

## Behavioral Tags

### List All Tags (grouped)
```bash
curl $BASE/tags
```

### Get Single Tag
```bash
curl $BASE/tags/piloerection
curl $BASE/tags/freeze
curl $BASE/tags/low_growl
```

### Apply Tag to Case
```bash
curl -X POST $BASE/cases/$CASE_ID/tags \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "tag_slug": "piloerection",
    "confidence": "observed",
    "timestamp_note": "0:15 in video"
  }'
```

Confidence values: `observed`, `probable`, `possible`

### List Tags on a Case
```bash
curl $BASE/cases/$CASE_ID/tags
```

### Remove Tag Application
```bash
curl -X DELETE $BASE/cases/$CASE_ID/tags/$TAG_APPLICATION_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

## Annotations

### Add Annotation
```bash
curl -X POST $BASE/cases/$CASE_ID/annotations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "annotation_type": "observation",
    "body": "Clear conflict freeze observed at the 15-second mark. Subject remained still for approximately 4 seconds.",
    "timestamp_start": 15.0,
    "timestamp_end": 19.0,
    "extra_data": {"intensity": "moderate"}
  }'
```

Annotation types: `observation`, `interpretation`, `concern`, `recommendation`

### List Annotations
```bash
curl $BASE/cases/$CASE_ID/annotations
```

---

## Comments

### Add Comment
```bash
curl -X POST $BASE/cases/$CASE_ID/comments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"body": "This looks like a classic stress response, not aggression."}'
```

### Reply to Comment
```bash
curl -X POST $BASE/cases/$CASE_ID/comments \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"body": "Agreed — the tail position confirms it.", "parent_id": "$COMMENT_ID"}'
```

### List Comments (threaded)
```bash
curl $BASE/cases/$CASE_ID/comments
```

---

## Expert Resolutions

> Requires `role=expert` or `role=admin`. Set via DB:
> ```sql
> UPDATE users SET role='expert' WHERE email='user@example.com';
> ```

### Submit Resolution
```bash
curl -X POST $BASE/cases/$CASE_ID/resolution \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "verdict": "concern",
    "summary": "Freeze + piloerection indicates a stress response to resource competition. Dog is communicating discomfort, not aggression.",
    "recommendations": "1) Separate resource-guarding dogs during play. 2) Monitor for escalation triggers.",
    "confidence_level": "high"
  }'
```

Verdicts: `safe`, `concern`, `escalation_risk`, `requires_intervention`  
Confidence: `high`, `medium`, `low`

### Get Resolution
```bash
curl $BASE/cases/$CASE_ID/resolution
```

---

## Media Uploads

### Upload Image
```bash
curl -X POST $BASE/cases/$CASE_ID/media \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/photo.jpg"
```

### Upload Video
```bash
curl -X POST $BASE/cases/$CASE_ID/media \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/video.mp4"
```

Accepted types: `image/jpeg`, `image/png`, `image/webp`, `video/mp4`, `video/quicktime`  
Limits: images 20 MB, videos 500 MB

### Alternative: /upload with case_id form field
```bash
curl -X POST $BASE/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/photo.jpg" \
  -F "case_id=$CASE_ID"
```

### List Case Media
```bash
curl $BASE/cases/$CASE_ID/media
```

---

## Users

### Get Own Profile
```bash
curl -H "Authorization: Bearer $TOKEN" $BASE/users/me
```

### Update Own Profile
```bash
curl -X PATCH $BASE/users/me \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"display_name": "New Name", "bio": "Dog trainer, 10 years experience"}'
```

### Public Profile
```bash
curl $BASE/users/trainertest
```

---

## Error Reference

All errors return:
```json
{"detail": "Human-readable message", "code": "machine_code"}
```

| HTTP | Code | Meaning |
|---|---|---|
| 400 | `validation_error` | Bad request data |
| 401 | `unauthorized` | Missing or invalid token |
| 403 | `forbidden` | Insufficient role |
| 404 | `not_found` | Resource not found |
| 409 | `conflict` | Duplicate (email, username, tag application) |
| 413 | `media_too_large` | File exceeds size limit |
| 415 | `unsupported_mime` | File type not accepted |

---

## OpenAPI Docs

Interactive API docs available at:
- Swagger UI: `http://127.0.0.1:8107/docs`
- OpenAPI JSON: `http://127.0.0.1:8107/openapi.json`
