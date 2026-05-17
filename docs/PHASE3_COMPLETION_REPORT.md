# BarkMind — Phase 3 Completion Report

**Date:** 2026-05-17  
**Status:** COMPLETE

---

## What Was Built

A fully hardened media processing pipeline with background thumbnail generation, multi-size
thumbnails, metadata extraction, storage abstraction, and a security-first upload flow.

---

## Backend Deliverables

### New Services

**`services/media_storage.py`** — Storage abstraction layer
- `StorageBackend` ABC defining the storage interface
- `LocalStorage` implementation with directory traversal prevention
- `S3Storage` stub for future upgrade (raises `NotImplementedError`)
- `get_storage()` factory that reads `MEDIA_BACKEND` config
- Path helpers: `case_original_dir`, `case_thumbnails_dir`, `case_derived_dir`, `case_frames_dir`
- `ensure_case_dirs()` creates the full 4-directory tree per case at upload time

**`services/media_processing.py`** — Processing engine
- `check_magic_bytes()` — validates file header bytes against 7+ blocked signatures + known image/video formats
- `extract_image_metadata()` — width/height via Pillow
- `extract_video_metadata()` — duration, dimensions, codec via ffprobe JSON output
- `generate_image_thumbnails()` — sm/md/lg via Pillow with EXIF orientation correction
- `generate_video_thumbnails()` — frame extraction via ffmpeg at 2s/1s/0s fallback + Pillow resize
- `extract_video_frames()` — foundation for future AI frame extraction (implemented, not yet called)
- `process_uploaded_media()` — async background task that orchestrates all processing and updates DB
- `FFMPEG_AVAILABLE` — startup check, disables video upload if ffmpeg not found

**`scripts/cleanup_media.py`** — Orphan cleanup
- Scans disk vs DB to find files without a `case_media` record
- Dry-run mode by default; `--delete` flag actually removes files
- `--verbose` flag for detailed output

### Updated Components

**`routers/media.py`** — Full rewrite with:
- Magic bytes validation for all uploads
- Early 415 rejection for dangerous file types (HTML, PHP, ELF, PE, scripts)
- Video mime check with ffmpeg gate
- `processing_status='pending'` on creation, `await db.commit()` before background task dispatch (fixes race condition)
- Three new thumbnail URL fields in response
- `GET /cases/{case_id}/media/{media_id}/status` — lightweight poll endpoint
- Delete endpoint removes all thumbnail files, not just original

**`schemas/media.py`** — Added:
- `ThumbnailSet(sm, md, lg)` — typed thumbnail URL set
- `MediaResponse.thumbnails` — all three sizes
- `MediaResponse.width_px`, `height_px`, `duration_seconds` — dimension and duration fields
- `MediaProcessingStatus` schema for poll endpoint

**`models/case_media.py`** — Added:
- `thumbnails: Mapped[dict]` — JSONB column for multi-size thumbnail paths

**Alembic migration** `759b2d6bccd0_add_media_thumbnails` — adds `thumbnails JSONB DEFAULT '{}'`

### Directory Structure Created Per Case

```
media/cases/{case_id}/
  original/       ← uploaded files (UUID-named, no original filename)
  thumbnails/     ← sm/md/lg JPEG thumbnails
  derived/        ← future: processed variants
  frames/         ← future: AI pipeline frame extracts
```

---

## Security Tests

| Test | Result |
|---|---|
| HTML file uploaded as `image/jpeg` | 415 `mime_mismatch` ✓ |
| PHP file uploaded as `image/png` | 415 `mime_mismatch` ✓ |
| Unsupported MIME type | 415 `unsupported_mime` ✓ |
| Valid JPEG upload | 201 Created ✓ |
| File too large | 413 `media_too_large` ✓ |
| Video upload without ffmpeg | 503 `service_unavailable` ✓ |
| Directory traversal in path | ValueError in storage layer ✓ |

---

## Processing Pipeline Test

| Stage | Result |
|---|---|
| Upload returns 201 (status=pending) | ✓ |
| Background task starts | ✓ |
| Thumbnails generated on disk (sm/md/lg) | ✓ (481, 999, 3136 bytes for test image) |
| DB record updated (status=ready) | ✓ |
| Status endpoint returns thumbnail URLs | ✓ |
| Width/height metadata populated | ✓ (800×600) |
| Race condition fix (commit before background task) | ✓ |

---

## Frontend Improvements

**`components/cases/MediaGallery.tsx`** rebuilt:
- Progressive image loading with spinner during load
- Image lightbox (click to view full size, ESC/click to close)
- Zoom button on hover
- Video player with poster image from generated thumbnail
- Processing status badge (pending / failed overlays)
- Video play indicator on thumbnail strip
- Media metadata row: filename, MIME, size, dimensions, duration
- Three-size thumbnail selection (`sm` for strip, `lg` for main view)
- `ThumbnailSet` support in `types.ts`

---

## Future Foundations

The following functions exist and are wired up but NOT called from the upload pipeline:

- **`extract_video_frames()`** — Frame extraction at configurable fps and max count
- **`case_derived_dir()`** — Directory structure for future processed variants
- **`case_frames_dir()`** — Directory structure pre-created per case

When Phase 4/5 multimodal AI is implemented, these will be called from the expert analysis endpoints.

---

## Port Conflict Note

Port 8107 remains occupied by `aegis-lite`. All Phase 3 testing was done on port 8108 via `.env.local` override. Functionality is fully confirmed — port resolution is a deployment concern only.
