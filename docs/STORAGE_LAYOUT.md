# BarkMind — Storage Layout

**Date:** 2026-05-17

---

## Root Configuration

```
MEDIA_ROOT=./media      ← relative to project root (dev default)
MEDIA_BACKEND=local     ← local | s3
```

Absolute path: `/home/jesse/infra/apps/BarkMind/media/`

---

## Directory Tree

```
{MEDIA_ROOT}/
  cases/
    {case_id}/
      original/
        {media_id}.{ext}            ← UUID-named, never uses original filename
      thumbnails/
        {media_id}_sm.jpg           ← 200px max, 1:1 aspect preserved
        {media_id}_md.jpg           ← 400px max, 1:1 aspect preserved [primary]
        {media_id}_lg.jpg           ← 800px max, 1:1 aspect preserved
      derived/                      ← empty; reserved for future processed variants
      frames/                       ← empty; reserved for AI frame extraction
```

### File Naming

All files use the `case_media.id` UUID as the filename base. The original filename is stored in the DB (`original_filename` column) for display only and is never used in filesystem paths.

### Extension Mapping

| MIME Type | Extension |
|---|---|
| image/jpeg | .jpg |
| image/png | .png |
| image/webp | .webp |
| video/mp4 | .mp4 |
| video/quicktime | .mov |
| video/webm | .webm |

---

## DB ↔ Disk Relationship

| DB Column | Disk Location |
|---|---|
| `stored_path` | `cases/{id}/original/{uuid}.{ext}` |
| `thumbnail_path` | `cases/{id}/thumbnails/{uuid}_md.jpg` |
| `thumbnails["sm"]` | `cases/{id}/thumbnails/{uuid}_sm.jpg` |
| `thumbnails["md"]` | `cases/{id}/thumbnails/{uuid}_md.jpg` |
| `thumbnails["lg"]` | `cases/{id}/thumbnails/{uuid}_lg.jpg` |

All paths stored as **relative to storage root** — not absolute.

---

## URL Serving

**Local (MVP):**
- Served via FastAPI `StaticFiles` mount at `/media`
- URL pattern: `/media/{rel_path}`
- Example: `/media/cases/{id}/original/{uuid}.jpg`
- Frontend prepends `/api-backend` to hit via Next.js proxy:
  - `http://127.0.0.1:3007/api-backend/media/cases/{id}/thumbnails/{uuid}_md.jpg`

**S3 (Future):**
- `stored_path` stored as `s3://bucket/{rel_path}`
- URLs returned as presigned CDN URLs (24h expiry or CloudFront)
- Zero frontend changes required

---

## Size Characteristics (Approximate)

| Type | Original | sm | md | lg |
|---|---|---|---|---|
| 1200×800 JPEG | 100–500 KB | 2–10 KB | 5–30 KB | 20–100 KB |
| 4K video (10s) | 50–200 MB | 5–20 KB | 15–50 KB | 30–100 KB |

Thumbnails are highly compressed JPEG (quality=85, optimize=True).

---

## Cleanup

**Orphan detection script:**
```bash
# Dry run (reports only)
python -m app.scripts.cleanup_media --verbose

# Delete orphans
python -m app.scripts.cleanup_media --delete
```

**Orphaned files:** Files on disk with no matching `case_media` record in the DB.
Common causes: failed uploads before DB write, manual DB deletions without file cleanup.

---

## Future: frames/ Directory

When multimodal AI analysis is enabled (Phase 4/5):

```
frames/
  {media_id}_frame_0001.jpg    ← 1 frame per 2s (configurable)
  {media_id}_frame_0002.jpg
  ...
  {media_id}_frame_0050.jpg    ← hard cap: 50 frames
```

Frame files are named with zero-padded 4-digit sequence numbers for deterministic ordering.

Total storage estimate per video:
- 50 frames × ~30 KB each ≈ 1.5 MB of frame storage per video

---

## Retention Policy

Current (MVP): Files are retained indefinitely.

Future (Phase 6 cleanup):
- Archived case → media soft-deleted flag
- Cleanup job deletes files for archived cases older than 90 days
- Frames directory purged after AI analysis is complete
