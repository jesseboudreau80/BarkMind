"""
Media upload router — Phase 3 hardened implementation.

Security hardening:
  - MIME validation: Content-Type header + file magic bytes
  - Size enforcement: streaming check, no full-buffer needed
  - Safe naming: UUID-based filenames only, original name stored in DB only
  - Directory traversal prevention: via StorageBackend._safe_resolve()
  - Executable blocking: magic bytes check rejects PE, ELF, scripts

Processing:
  - Uploads complete immediately (201 returned)
  - Background task generates thumbnails + extracts metadata
  - Client polls processing_status via GET /cases/{id}/media
"""
import logging
import uuid
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from uuid import UUID as PyUUID

from app.deps import CurrentUser, DB
from app.models.case import Case
from app.models.case_media import CaseMedia
from app.schemas.media import MediaResponse, ThumbnailSet
from app.services.media_processing import (
    ALLOWED_MIMES,
    FFMPEG_AVAILABLE,
    IMAGE_MIMES,
    MAGIC_READ_BYTES,
    check_magic_bytes,
    max_bytes_for_mime,
    process_uploaded_media,
)
from app.services.media_storage import (
    case_original_dir,
    ensure_case_dirs,
    get_storage,
)

log = logging.getLogger("barkmind.media")

router = APIRouter(tags=["media"])


def _build_media_response(record: CaseMedia) -> MediaResponse:
    storage = get_storage()
    thumbs = record.thumbnails or {}
    return MediaResponse(
        id=record.id,
        case_id=record.case_id,
        media_type=record.media_type,
        original_filename=record.original_filename,
        mime_type=record.mime_type,
        size_bytes=record.size_bytes,
        width_px=record.width_px,
        height_px=record.height_px,
        duration_seconds=record.duration_seconds,
        processing_status=record.processing_status,
        thumbnail_url=storage.url(record.thumbnail_path) if record.thumbnail_path else None,
        thumbnails=ThumbnailSet(
            sm=storage.url(thumbs["sm"]) if "sm" in thumbs else None,
            md=storage.url(thumbs["md"]) if "md" in thumbs else None,
            lg=storage.url(thumbs["lg"]) if "lg" in thumbs else None,
        ),
        url=storage.url(record.stored_path),
        created_at=record.created_at,
    )


@router.post(
    "/cases/{case_id}/media",
    response_model=MediaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_case_media(
    case_id: PyUUID,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: DB,
    user: CurrentUser,
):
    """
    Upload an image or video to a case.

    Validates MIME type (header + magic bytes) and file size before writing.
    Returns 201 immediately; thumbnail generation runs in the background.
    Poll GET /cases/{case_id}/media/{media_id}/status for processing_status='ready'.
    """
    # ── Verify case exists ────────────────────────────────────────────────────
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    if case_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    # ── MIME validation: declared type ────────────────────────────────────────
    mime = (file.content_type or "").strip().lower()
    if mime not in ALLOWED_MIMES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "detail": (
                    f"Unsupported media type: {mime!r}. "
                    "Accepted: image/jpeg, image/png, image/webp, "
                    "video/mp4, video/quicktime, video/webm"
                ),
                "code": "unsupported_mime",
            },
        )

    # Video upload requires ffmpeg
    if mime not in IMAGE_MIMES and not FFMPEG_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "detail": "Video uploads are temporarily unavailable (ffmpeg not found).",
                "code": "service_unavailable",
            },
        )

    media_type, ext = ALLOWED_MIMES[mime]
    max_size = max_bytes_for_mime(mime)
    storage = get_storage()

    # ── Read header bytes for magic-bytes validation ───────────────────────────
    header = await file.read(MAGIC_READ_BYTES)
    if len(header) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "File is too small to be valid.", "code": "invalid_file"},
        )

    if not check_magic_bytes(header, mime):
        log.warning(
            "Magic bytes mismatch: file=%s declared=%s header=%r",
            file.filename,
            mime,
            header[:8],
        )
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "detail": (
                    "File content does not match declared MIME type. "
                    "The file appears to have been misidentified or manipulated."
                ),
                "code": "mime_mismatch",
            },
        )

    # ── Prepare storage paths ─────────────────────────────────────────────────
    media_id = uuid.uuid4()
    case_id_str = str(case_id)
    media_id_str = str(media_id)

    ensure_case_dirs(storage, case_id_str)
    rel_path = f"{case_original_dir(case_id_str)}/{media_id_str}{ext}"
    abs_path = storage.absolute_path(rel_path)

    # ── Stream file to disk with size enforcement ─────────────────────────────
    size = len(header)
    try:
        with open(abs_path, "wb") as out_f:
            out_f.write(header)
            while chunk := await file.read(256 * 1024):
                size += len(chunk)
                if size > max_size:
                    out_f.close()
                    abs_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail={
                            "detail": (
                                f"File exceeds the {max_size // (1024 * 1024)} MB limit."
                            ),
                            "code": "media_too_large",
                        },
                    )
                out_f.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        abs_path.unlink(missing_ok=True)
        log.error("Upload write failed for %s/%s: %s", case_id, media_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": "Failed to save uploaded file.", "code": "storage_error"},
        )

    log.info("Uploaded %d bytes → %s", size, rel_path)

    # ── Persist DB record with processing_status='pending' ────────────────────
    record = CaseMedia(
        id=media_id,
        case_id=case_id,
        uploader_id=user.id,
        media_type=media_type,
        original_filename=file.filename,
        stored_path=rel_path,
        mime_type=mime,
        size_bytes=size,
        processing_status="pending",
        thumbnails={},
    )
    db.add(record)
    # Commit now so the background task can find this record in its own session.
    # Background tasks start before get_db() commits at request teardown.
    await db.commit()

    # ── Schedule background processing ───────────────────────────────────────
    background_tasks.add_task(
        process_uploaded_media,
        media_id=media_id_str,
        stored_path=rel_path,
        media_type=media_type,
        case_id=case_id_str,
        storage_root=storage.absolute_path(""),
    )

    return _build_media_response(record)


@router.get("/cases/{case_id}/media")
async def list_case_media(case_id: PyUUID, db: DB):
    """List all media for a case, ordered by upload time."""
    result = await db.execute(
        select(CaseMedia)
        .where(CaseMedia.case_id == case_id)
        .order_by(CaseMedia.created_at.asc())
    )
    return [_build_media_response(m) for m in result.scalars().all()]


@router.get("/cases/{case_id}/media/{media_id}/status")
async def get_media_processing_status(case_id: PyUUID, media_id: PyUUID, db: DB):
    """
    Lightweight poll endpoint for processing status.

    Returns once processing_status transitions to 'ready' or 'failed'.
    """
    result = await db.execute(
        select(CaseMedia).where(
            CaseMedia.id == media_id,
            CaseMedia.case_id == case_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Media not found", "code": "not_found"},
        )

    storage = get_storage()
    thumbs = record.thumbnails or {}
    return {
        "id": str(record.id),
        "processing_status": record.processing_status,
        "thumbnail_url": storage.url(record.thumbnail_path) if record.thumbnail_path else None,
        "thumbnails": {k: storage.url(v) for k, v in thumbs.items() if v},
        "width_px": record.width_px,
        "height_px": record.height_px,
        "duration_seconds": record.duration_seconds,
    }


@router.delete(
    "/cases/{case_id}/media/{media_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_media(case_id: PyUUID, media_id: PyUUID, db: DB, user: CurrentUser):
    """Delete a media record and all associated files (original + all thumbnail sizes)."""
    result = await db.execute(
        select(CaseMedia).where(
            CaseMedia.id == media_id,
            CaseMedia.case_id == case_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Media not found", "code": "not_found"},
        )
    if record.uploader_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Not authorized to delete this media.", "code": "forbidden"},
        )

    storage = get_storage()
    storage.delete(record.stored_path)
    for thumb_path in (record.thumbnails or {}).values():
        if thumb_path:
            storage.delete(thumb_path)

    await db.delete(record)
    log.info("Deleted media %s (case=%s)", media_id, case_id)


@router.post("/upload", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media_alias(
    file: UploadFile,
    case_id: str = Form(...),
    background_tasks: BackgroundTasks = None,
    db: DB = None,
    user: CurrentUser = None,
):
    """Alias: POST /upload with case_id as form field → POST /cases/{case_id}/media."""
    try:
        case_uuid = PyUUID(case_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={"detail": "Invalid case_id", "code": "validation_error"},
        )
    return await upload_case_media(case_uuid, file, background_tasks, db, user)
