# BarkMind — Media Pipeline Plan

**Date:** 2026-05-17  
**MVP Storage:** Local disk (structured path)  
**Production Target:** S3-compatible object storage (Cloudflare R2 or AWS S3)

---

## Design Goals

- Media upload works on Day 1 with local disk — no S3 dependency
- Storage backend is swappable via env var (`MEDIA_BACKEND=local|s3`)
- Thumbnails generated automatically (background task)
- Uploads validated before storage — no garbage files
- Paths are deterministic and case-scoped
- Docker-ready: storage root configurable via env var

---

## Storage Layout (Local)

```
/var/barkmind/media/
  cases/
    {case_id}/
      original/
        {media_id}.{ext}          ← uploaded file
      thumbnails/
        {media_id}_thumb.jpg      ← generated thumbnail
```

Env var: `MEDIA_ROOT=/var/barkmind/media`  
Dev override: `MEDIA_ROOT=./media`

---

## Accepted MIME Types

| MIME | Extension | Max Size |
|---|---|---|
| `image/jpeg` | .jpg, .jpeg | 20 MB |
| `image/png` | .png | 20 MB |
| `image/webp` | .webp | 20 MB |
| `video/mp4` | .mp4 | 500 MB |
| `video/quicktime` | .mov | 500 MB |

Rejection behavior: HTTP 415 with `{"code": "unsupported_mime"}`.

---

## Upload Flow

```
Client
  → POST /cases/{id}/media (multipart/form-data)
  → FastAPI endpoint
    → Validate MIME against allowlist
    → Validate size against per-type cap
    → Generate media_id (UUID)
    → Write original file to {MEDIA_ROOT}/cases/{case_id}/original/{media_id}.{ext}
    → Insert case_media row (processing_status = 'pending')
    → Enqueue background task: generate_thumbnail(media_id)
    → Return 201 with media record
  → Background task runs (FastAPI BackgroundTasks)
    → Image: Pillow resize to max 800px width, save as JPEG
    → Video: ffmpeg -ss 2 -i {input} -frames:v 1 -q:v 2 {output}
    → Update case_media.thumbnail_path + processing_status = 'ready'
    → On failure: processing_status = 'failed', log error
```

---

## Thumbnail Generation

### Images — Pillow

```python
from PIL import Image

def generate_image_thumbnail(source_path: str, dest_path: str, max_width: int = 800):
    with Image.open(source_path) as img:
        img.thumbnail((max_width, max_width), Image.LANCZOS)
        img.convert("RGB").save(dest_path, "JPEG", quality=85)
```

### Video — ffmpeg

```bash
ffmpeg -ss 2 -i {source} -frames:v 1 -vf "scale=800:-1" -q:v 2 {dest}.jpg
```

Frame at 2 seconds. Falls back to frame 0 if video is under 2 seconds.

ffmpeg must be present in PATH. Checked at startup — warning logged if missing, video upload disabled.

---

## Media Serving

**MVP:** FastAPI static file mount.

```python
from fastapi.staticfiles import StaticFiles
app.mount("/media", StaticFiles(directory=MEDIA_ROOT), name="media")
```

Media URLs:
```
https://barkmind-api.jesseboudreau.com/media/cases/{case_id}/original/{media_id}.mp4
https://barkmind-api.jesseboudreau.com/media/cases/{case_id}/thumbnails/{media_id}_thumb.jpg
```

**Production upgrade path:** Replace StaticFiles mount with redirect to CDN/R2 presigned URL.
No frontend changes required — just swap the URL generation logic in `case_media` model.

---

## S3 Upgrade Path (Phase 3+)

When `MEDIA_BACKEND=s3`:

- Upload stream goes to S3 via `boto3` / `aioboto3`
- `stored_path` stored as `s3://bucket/cases/{case_id}/original/{media_id}.{ext}`
- Thumbnails uploaded to S3 after generation
- Media served via presigned URL (24h expiry) or CloudFront

No ORM changes required — `stored_path` and `thumbnail_path` remain strings.

---

## Validation Rules

```python
ALLOWED_MIMES = {
    "image/jpeg", "image/png", "image/webp",
    "video/mp4", "video/quicktime"
}

MAX_SIZE = {
    "image": 20 * 1024 * 1024,   # 20 MB
    "video": 500 * 1024 * 1024,  # 500 MB
}
```

Validation order:
1. Content-Type header check (fast reject)
2. File magic bytes check (prevent MIME spoofing)
3. Streaming size check (don't buffer entire file to check size)

---

## Security Considerations

- Files are stored by UUID, not original filename
- Original filename stored in DB for display only — never used in paths
- MIME validated by both header and file magic
- Upload directory is NOT inside the web root (no direct execution)
- No untrusted filenames touch the filesystem

---

## Future: AI Media Analysis (Phase 5+)

When multimodal AI analysis is enabled:

```
case_media.id → AI analysis job queue
  → Extract frames at N fps
  → Send frames to Claude API (multimodal)
  → Store behavioral observations per frame
  → Aggregate into case-level behavioral score
```

The `case_media` table has `duration_seconds`, `width_px`, `height_px` to support frame-rate-based
extraction calculations without re-probing files.

---

## Operational Notes

- `MEDIA_ROOT` must exist and be writable at startup — checked in `start.sh`
- Background thumbnail failures are logged but do not affect case availability
- `processing_status` polling: frontend polls `/cases/{id}/media` until `ready`
- Orphaned media files (DB deleted, file remains) handled by a periodic cleanup script (Phase 6)
