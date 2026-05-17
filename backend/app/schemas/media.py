from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ThumbnailSet(BaseModel):
    """Three-tier thumbnail URLs: sm (200px), md (400px), lg (800px)."""
    sm: str | None = None
    md: str | None = None
    lg: str | None = None


class MediaResponse(BaseModel):
    id: UUID
    case_id: UUID
    media_type: str
    original_filename: str | None
    mime_type: str | None
    size_bytes: int | None
    # Phase 3: dimensions and duration
    width_px: int | None = None
    height_px: int | None = None
    duration_seconds: float | None = None
    # Processing state
    processing_status: str
    # Primary thumbnail URL (medium size)
    thumbnail_url: str | None
    # All thumbnail sizes
    thumbnails: ThumbnailSet = ThumbnailSet()
    # Original file URL
    url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MediaProcessingStatus(BaseModel):
    """Lightweight poll response for upload processing status."""
    id: UUID
    processing_status: str
    thumbnail_url: str | None
    thumbnails: dict[str, str] = {}
    width_px: int | None = None
    height_px: int | None = None
    duration_seconds: float | None = None
