# BarkMind — Media Architecture

**Date:** 2026-05-17  
**Phase:** 3 Complete

---

## Layers

```
HTTP Upload Request
    │
    ▼
[Router: media.py]
    ├── Case existence check
    ├── MIME declaration check (Content-Type header)
    ├── ffmpeg gate (video MIME)
    ├── Read 16 header bytes
    ├── Magic bytes validation → 415 if mismatch
    ├── Streaming write to disk via StorageBackend
    ├── Size enforcement (streaming, no full-buffer)
    ├── CaseMedia DB insert (processing_status='pending')
    ├── await db.commit() ← required before background dispatch
    ├── Schedule background task
    └── Return 201 (pending)

[Background Task: process_uploaded_media()]
    ├── asyncio.to_thread(_process_sync)
    │     ├── Image: extract_image_metadata() + generate_image_thumbnails()
    │     └── Video: extract_video_metadata() + generate_video_thumbnails()
    ├── Convert absolute thumbnail paths → relative
    └── DB update: processing_status='ready', thumbnails={}, thumbnail_path, dimensions

[Client Poll]
    GET /cases/{id}/media/{media_id}/status
    └── Returns processing_status + thumbnail URLs when ready
```

---

## Storage Abstraction

```python
class StorageBackend(ABC):
    write_stream(rel_path, data)   → None
    delete(rel_path)               → None
    exists(rel_path)               → bool
    url(rel_path)                  → str    # URL for API client
    absolute_path(rel_path)        → Path   # Local backends only
    makedirs(rel_dir)              → None
```

**LocalStorage** — MVP implementation
- Root: `MEDIA_ROOT` env var (defaults to `./media` relative to project root)
- All paths validated against root (directory traversal prevention)
- URLs: `/media/{rel_path}` served via FastAPI StaticFiles

**S3Storage** — Stub (future)
- Activated by `MEDIA_BACKEND=s3`
- All methods raise `NotImplementedError`
- No ORM changes needed: `stored_path` and `thumbnail_path` are just strings

---

## Thumbnail Strategy

Three sizes generated for every media item:

| Size Key | Pixels | Use Case |
|---|---|---|
| `sm` | max 200×200 | Thumbnail strip, case cards |
| `md` | max 400×400 | Primary stored in `thumbnail_path` |
| `lg` | max 800×800 | Main gallery viewer, lightbox |

**Image generation** (Pillow):
1. Open source file
2. Apply EXIF orientation correction (`ImageOps.exif_transpose`)
3. Convert to RGB (handles RGBA, palette modes)
4. `img.thumbnail((max_dim, max_dim), Image.LANCZOS)` — aspect-preserving
5. Save as JPEG, quality=85, optimize=True

**Video generation** (ffmpeg + Pillow):
1. Seek to 2.0s (fallback: 1.0s, 0.5s, 0.0s based on duration)
2. `ffmpeg -ss {seek} -i {input} -frames:v 1 -vf scale={md_width}:-2 -q:v 2 {raw_frame}`
3. Use Pillow to generate all three sizes from the raw frame
4. Delete raw frame intermediate file

---

## Magic Bytes Validation

16 header bytes checked against known signatures:

| Format | Signature |
|---|---|
| JPEG | `FF D8 FF` |
| PNG | `89 50 4E 47 0D 0A 1A 0A` |
| WebP | `RIFF....WEBP` |
| MP4/MOV | `ftyp`/`moov`/`mdat` atom at offset 4 |
| WebM | `1A 45 DF A3` (EBML) |

Blocked signatures (rejected regardless of declared MIME):
- `<!DOCTYPE`, `<html` — HTML
- `<?php` — PHP
- `MZ` — Windows PE executable
- `\x7fELF` — Linux ELF executable
- `PK\x03\x04` — ZIP archive
- `%PDF` — PDF
- `#!/` — Script shebang

---

## Future AI Pipeline Foundation

The Phase 3 implementation pre-creates directories and implements (but does not call) the frame extraction pipeline:

```
media/cases/{case_id}/
  original/         ← uploaded files (Phase 1+)
  thumbnails/       ← sm/md/lg thumbnails (Phase 3)
  derived/          ← future processed variants
  frames/           ← future AI frame extracts
```

**`extract_video_frames(src, frames_dir, media_id, fps=0.5, max_frames=50)`**

When called (Phase 4/5):
- Extracts 1 frame per 2 seconds (configurable)
- Hard cap at 50 frames (cost control)
- Stored as `{media_id}_frame_{n:04d}.jpg`
- Returns list of absolute paths for Claude API call

---

## Operational Notes

- `FFMPEG_AVAILABLE` checked at startup: video upload disabled if ffmpeg not in PATH
- Processing failures set `processing_status='failed'` (does not affect case availability)
- Background tasks cannot be cancelled once dispatched (file + DB record already exist)
- Race condition fix: `await db.commit()` in router before `background_tasks.add_task()`
- Cleanup script: `python -m app.scripts.cleanup_media --verbose [--delete]`

---

## S3 Upgrade Path

Zero code changes required in routers or models. Only `get_storage()` in `services/media_storage.py` needs updating when `S3Storage` is implemented:

1. Implement `S3Storage.write_stream()` using `aioboto3`
2. Implement `S3Storage.url()` to return presigned CDN URLs
3. Set `MEDIA_BACKEND=s3` in environment
4. Media URLs in API responses automatically reflect the new storage
