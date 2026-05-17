"""
Media processing service for BarkMind.

Handles:
- File magic-bytes validation (MIME spoofing prevention)
- Image thumbnail generation via Pillow (3 sizes)
- Video thumbnail generation via ffmpeg (frame at seek point)
- Image metadata extraction (dimensions)
- Video metadata extraction (duration, dimensions, codec) via ffprobe
- Frame extraction foundation (directories + function, not yet called)
- Background processing orchestration via asyncio.to_thread
"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import uuid
from pathlib import Path
from typing import Optional

log = logging.getLogger("barkmind.media")

# ─── Thumbnail sizes ───────────────────────────────────────────────────────────

THUMBNAIL_SIZES: dict[str, int] = {
    "sm": 200,   # small: card thumbnails, strip previews
    "md": 400,   # medium: primary thumbnail stored in case_media.thumbnail_path
    "lg": 800,   # large: preview/lightbox quality
}

# ─── Allowed MIME types ────────────────────────────────────────────────────────

IMAGE_MIMES: set[str] = {"image/jpeg", "image/png", "image/webp"}
VIDEO_MIMES: set[str] = {"video/mp4", "video/quicktime", "video/webm"}
ALLOWED_MIMES: dict[str, tuple[str, str]] = {
    "image/jpeg":    ("image", ".jpg"),
    "image/png":     ("image", ".png"),
    "image/webp":    ("image", ".webp"),
    "video/mp4":     ("video", ".mp4"),
    "video/quicktime": ("video", ".mov"),
    "video/webm":    ("video", ".webm"),
}

IMAGE_MAX_BYTES: int = 20 * 1024 * 1024    # 20 MB
VIDEO_MAX_BYTES: int = 500 * 1024 * 1024   # 500 MB


def max_bytes_for_mime(mime: str) -> int:
    if mime in IMAGE_MIMES:
        return IMAGE_MAX_BYTES
    return VIDEO_MAX_BYTES


# ─── Magic bytes validation ────────────────────────────────────────────────────

# Minimum header bytes to read for validation
MAGIC_READ_BYTES = 16

# Known dangerous signatures that should NEVER be accepted
_BLOCKED_SIGNATURES: tuple[bytes, ...] = (
    b"<!DOCTYPE",    # HTML
    b"<html",        # HTML
    b"<?php",        # PHP
    b"MZ",           # Windows PE executable
    b"\x7fELF",      # ELF executable (Linux)
    b"PK\x03\x04",  # ZIP archive (could be JAR, DOCX etc.)
    b"%PDF",         # PDF
    b"#!/",          # Script shebang
)


def check_magic_bytes(header: bytes, declared_mime: str) -> bool:
    """
    Validate that file header bytes match the declared MIME type.

    This is a defense-in-depth check against MIME spoofing.
    A client declaring image/jpeg but uploading a PHP script will be rejected here.
    """
    if len(header) < 4:
        return False

    # Reject known-dangerous file types regardless of declared MIME
    for blocked in _BLOCKED_SIGNATURES:
        if header[: len(blocked)].lower() == blocked.lower():
            log.warning("Blocked dangerous file signature: %r", header[:8])
            return False

    if declared_mime == "image/jpeg":
        return header[:3] == b"\xff\xd8\xff"

    if declared_mime == "image/png":
        return header[:8] == b"\x89PNG\r\n\x1a\n"

    if declared_mime == "image/webp":
        return header[:4] == b"RIFF" and header[8:12] == b"WEBP"

    if declared_mime in ("video/mp4", "video/quicktime"):
        # MP4/MOV: 4-byte big-endian size, then 'ftyp' atom type at offset 4
        # Some files have other atoms first (free, wide, mdat) — check a wider range
        # Check for ftyp at offset 4 (most common position)
        if header[4:8] == b"ftyp":
            return True
        # Check for other valid first atoms (QuickTime containers)
        if header[4:8] in (b"moov", b"mdat", b"free", b"wide", b"pnot"):
            return True
        # Some MP4/MOV files start with a 0-length atom
        if header[:4] == b"\x00\x00\x00\x00":
            return True
        return False

    if declared_mime == "video/webm":
        # EBML signature
        return header[:4] == b"\x1a\x45\xdf\xa3"

    # Unknown MIME — reject
    return False


# ─── Image metadata ────────────────────────────────────────────────────────────

def extract_image_metadata(src_path: Path) -> dict:
    """Extract width, height from an image file using Pillow."""
    try:
        from PIL import Image
        with Image.open(src_path) as img:
            return {"width_px": img.width, "height_px": img.height}
    except Exception as exc:
        log.warning("Failed to extract image metadata from %s: %s", src_path, exc)
        return {}


# ─── Video metadata ────────────────────────────────────────────────────────────

def extract_video_metadata(src_path: Path) -> dict:
    """Extract duration, dimensions, and codec from a video using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_streams",
                "-show_format",
                str(src_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            log.warning("ffprobe failed for %s: %s", src_path, result.stderr[:200])
            return {}

        info = json.loads(result.stdout)
        meta: dict = {}

        # Find the video stream
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                meta["width_px"] = stream.get("width")
                meta["height_px"] = stream.get("height")
                meta["codec_name"] = stream.get("codec_name")
                # Duration from stream or format
                duration_str = stream.get("duration") or info.get("format", {}).get("duration")
                if duration_str:
                    meta["duration_seconds"] = float(duration_str)
                break

        # Fallback duration from format
        if "duration_seconds" not in meta:
            fmt_duration = info.get("format", {}).get("duration")
            if fmt_duration:
                meta["duration_seconds"] = float(fmt_duration)

        return meta

    except subprocess.TimeoutExpired:
        log.error("ffprobe timed out on %s", src_path)
        return {}
    except Exception as exc:
        log.warning("Failed to extract video metadata from %s: %s", src_path, exc)
        return {}


# ─── Image thumbnails ──────────────────────────────────────────────────────────

def generate_image_thumbnails(
    src_path: Path,
    dest_dir: Path,
    media_id: str,
) -> dict[str, str]:
    """
    Generate sm/md/lg JPEG thumbnails from an image file.

    Returns dict mapping size key → relative path within media root.
    """
    from PIL import Image, ImageOps

    thumbnails: dict[str, str] = {}
    dest_dir.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(src_path) as img:
            # Normalize: handle EXIF orientation, convert to RGB
            img = ImageOps.exif_transpose(img)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            for size_key, max_dim in THUMBNAIL_SIZES.items():
                thumb = img.copy()
                thumb.thumbnail((max_dim, max_dim), Image.LANCZOS)
                filename = f"{media_id}_{size_key}.jpg"
                out_path = dest_dir / filename
                thumb.save(out_path, "JPEG", quality=85, optimize=True)

                # Compute relative path from the storage root
                # dest_dir is absolute; we need to get the part after media_root
                # We store the path relative to storage root as: cases/{id}/thumbnails/{file}
                thumbnails[size_key] = str(out_path)

        return thumbnails

    except Exception as exc:
        log.error("Image thumbnail generation failed for %s: %s", src_path, exc)
        return {}


# ─── Video thumbnails ──────────────────────────────────────────────────────────

def _ffmpeg_extract_frame(src_path: Path, out_path: Path, seek_seconds: float, width: int = 400) -> bool:
    """Extract a single video frame at seek_seconds, scaled to width."""
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-v", "quiet",
                "-ss", str(seek_seconds),
                "-i", str(src_path),
                "-frames:v", "1",
                "-vf", f"scale={width}:-2",
                "-q:v", "2",
                "-y",
                str(out_path),
            ],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            log.warning("ffmpeg frame extract failed at %.1fs: %s", seek_seconds, result.stderr[:200])
            return False
        return out_path.exists() and out_path.stat().st_size > 0
    except subprocess.TimeoutExpired:
        log.error("ffmpeg timed out extracting frame from %s", src_path)
        return False
    except Exception as exc:
        log.error("ffmpeg error: %s", exc)
        return False


def generate_video_thumbnails(
    src_path: Path,
    dest_dir: Path,
    media_id: str,
    duration_seconds: Optional[float] = None,
) -> dict[str, str]:
    """
    Generate sm/md/lg JPEG thumbnails from a video using ffmpeg + Pillow.

    Strategy:
    1. Extract a frame at 2s (or 1s, or 0s as fallback)
    2. Resize to md size with ffmpeg
    3. Use Pillow to derive sm and lg from md frame
    """
    from PIL import Image

    dest_dir.mkdir(parents=True, exist_ok=True)
    thumbnails: dict[str, str] = {}

    # Choose seek time — use min(2s, duration-0.5s)
    seek_candidates = [2.0, 1.0, 0.5, 0.0]
    if duration_seconds is not None and duration_seconds < 2.0:
        seek_candidates = [max(0.0, duration_seconds * 0.5), 0.0]

    # Extract medium frame via ffmpeg
    md_path = dest_dir / f"{media_id}_md_raw.jpg"
    frame_extracted = False

    for seek in seek_candidates:
        if _ffmpeg_extract_frame(src_path, md_path, seek, width=THUMBNAIL_SIZES["md"]):
            frame_extracted = True
            break

    if not frame_extracted:
        log.error("Could not extract any frame from video %s", src_path)
        return {}

    # Use Pillow to generate all three sizes from the extracted frame
    try:
        with Image.open(md_path) as base:
            base = base.convert("RGB")

            for size_key, max_dim in THUMBNAIL_SIZES.items():
                thumb = base.copy()
                thumb.thumbnail((max_dim, max_dim), Image.LANCZOS)
                filename = f"{media_id}_{size_key}.jpg"
                out_path = dest_dir / filename
                thumb.save(out_path, "JPEG", quality=85, optimize=True)
                thumbnails[size_key] = str(out_path)

    except Exception as exc:
        log.error("Failed to resize video frame thumbnails: %s", exc)
        return {}
    finally:
        # Clean up the intermediate raw frame
        if md_path.exists():
            md_path.unlink()

    return thumbnails


# ─── Frame extraction foundation (future AI pipeline) ─────────────────────────

def extract_video_frames(
    src_path: Path,
    frames_dir: Path,
    media_id: str,
    fps: float = 0.5,
    max_frames: int = 50,
) -> list[str]:
    """
    Extract frames from a video at a given frame rate.

    This function is wired up but NOT called from the upload pipeline yet.
    It exists as the foundation for the Phase 4/5 multimodal AI analysis.

    Args:
        src_path: Absolute path to the source video file.
        frames_dir: Directory to write frame JPEGs into.
        media_id: Used for naming frames (f"{media_id}_frame_{n:04d}.jpg").
        fps: Frames per second to extract (0.5 = 1 frame per 2 seconds).
        max_frames: Safety cap to prevent runaway storage usage.

    Returns:
        List of absolute paths to extracted frame files.
    """
    frames_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = str(frames_dir / f"{media_id}_frame_%04d.jpg")

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-v", "quiet",
                "-i", str(src_path),
                "-vf", f"fps={fps},scale=800:-2",
                "-frames:v", str(max_frames),
                "-q:v", "3",
                "-y",
                output_pattern,
            ],
            capture_output=True,
            timeout=120,
        )
        if result.returncode != 0:
            log.error("Frame extraction failed: %s", result.stderr[:300])
            return []

        # Collect generated frames in order
        frames = sorted(frames_dir.glob(f"{media_id}_frame_*.jpg"))
        log.info("Extracted %d frames from %s", len(frames), src_path.name)
        return [str(f) for f in frames]

    except subprocess.TimeoutExpired:
        log.error("Frame extraction timed out for %s", src_path)
        return []
    except Exception as exc:
        log.error("Frame extraction error: %s", exc)
        return []


# ─── Background processing task ───────────────────────────────────────────────

async def process_uploaded_media(
    media_id: str,
    stored_path: str,
    media_type: str,
    case_id: str,
    storage_root: Path,
) -> None:
    """
    Background task: generate thumbnails and extract metadata after upload.

    Runs in a thread pool via asyncio.to_thread to avoid blocking the event loop.
    Updates the CaseMedia record directly in its own DB session.
    """
    from app.database import AsyncSessionLocal
    from app.models.case_media import CaseMedia
    from sqlalchemy import select

    log.info("Processing media %s (type=%s)", media_id, media_type)

    def _process_sync() -> dict:
        """All blocking I/O runs here in a thread."""
        src_path = storage_root / stored_path
        if not src_path.exists():
            raise FileNotFoundError(f"Source file missing: {src_path}")

        # Absolute thumbnails directory
        thumbs_abs = storage_root / f"cases/{case_id}/thumbnails"
        thumbs_abs.mkdir(parents=True, exist_ok=True)

        result: dict = {}

        if media_type == "image":
            # Image metadata
            result.update(extract_image_metadata(src_path))
            # Thumbnails
            raw_thumbs = generate_image_thumbnails(src_path, thumbs_abs, media_id)
        else:
            # Video metadata first (need duration for frame seek)
            meta = extract_video_metadata(src_path)
            result.update(meta)
            duration = meta.get("duration_seconds")
            # Thumbnails
            raw_thumbs = generate_video_thumbnails(src_path, thumbs_abs, media_id, duration)

        # Convert absolute thumbnail paths → relative paths (from storage_root)
        thumbnails: dict[str, str] = {}
        for size_key, abs_path in raw_thumbs.items():
            try:
                rel = str(Path(abs_path).relative_to(storage_root))
                thumbnails[size_key] = rel
            except ValueError:
                thumbnails[size_key] = abs_path

        result["thumbnails"] = thumbnails
        # Primary thumbnail = medium size
        result["thumbnail_path"] = thumbnails.get("md", thumbnails.get("lg", ""))
        return result

    # Run blocking processing in thread pool
    try:
        processing_result = await asyncio.to_thread(_process_sync)
        status = "ready"
        log.info("Media %s processed successfully: %s", media_id, processing_result.get("thumbnails", {}).keys())
    except Exception as exc:
        log.error("Media processing failed for %s: %s", media_id, exc, exc_info=True)
        processing_result = {}
        status = "failed"

    # Update database record in a new session
    try:
        import uuid as _uuid
        from sqlalchemy.orm.attributes import flag_modified

        media_uuid = _uuid.UUID(media_id)

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(CaseMedia).where(CaseMedia.id == media_uuid)
            )
            record = result.scalar_one_or_none()
            if record is None:
                log.warning("Media record %s not found for status update", media_id)
                return

            record.processing_status = status
            record.thumbnails = processing_result.get("thumbnails", {})
            record.thumbnail_path = processing_result.get("thumbnail_path") or None
            record.width_px = processing_result.get("width_px")
            record.height_px = processing_result.get("height_px")
            record.duration_seconds = processing_result.get("duration_seconds")

            # Force SQLAlchemy to detect JSONB mutation
            flag_modified(record, "thumbnails")

            await db.commit()
            log.info(
                "Media %s DB record updated → status=%s thumbnails=%s",
                media_id,
                status,
                list((record.thumbnails or {}).keys()),
            )
    except Exception as exc:
        log.error("Failed to update media record %s after processing: %s", media_id, exc, exc_info=True)


# ─── ffmpeg availability check ────────────────────────────────────────────────

def check_ffmpeg() -> bool:
    """Return True if ffmpeg/ffprobe are available in PATH."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


FFMPEG_AVAILABLE: bool = check_ffmpeg()
