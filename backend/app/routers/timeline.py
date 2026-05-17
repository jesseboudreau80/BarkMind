"""
Timeline marker routes for video case annotation.

Timeline markers pin named behavioral events to specific video timestamps,
building a structured behavioral timeline that:
- Guides expert review
- Supports future frame extraction for AI analysis
- Provides dataset-quality temporal labels
"""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.case import Case
from app.models.case_media import CaseMedia
from app.models.timeline_marker import TimelineMarker
from app.schemas.timeline import (
    MARKER_TYPES,
    TimelineMarkerCreate,
    TimelineMarkerPatch,
    TimelineMarkerResponse,
)

log = logging.getLogger("barkmind.timeline")
router = APIRouter(prefix="/cases", tags=["timeline"])


def _serialize(m: TimelineMarker) -> TimelineMarkerResponse:
    return TimelineMarkerResponse(
        id=m.id,
        case_id=m.case_id,
        media_id=m.media_id,
        author_username=m.author.username,
        timestamp_seconds=m.timestamp_seconds,
        label=m.label,
        marker_type=m.marker_type,
        notes=m.notes,
        is_expert=m.is_expert,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


@router.get("/{case_id}/timeline")
async def list_timeline_markers(
    case_id: UUID,
    db: DB,
    media_id: UUID | None = Query(None, description="Filter to a specific media file"),
    marker_type: str | None = Query(None, description="Filter by marker type"),
    expert_only: bool = Query(False, description="Return only expert markers"),
):
    """
    List all timeline markers for a case, ordered by timestamp.

    Markers represent named behavioral events at specific video timestamps.
    """
    stmt = (
        select(TimelineMarker)
        .where(TimelineMarker.case_id == case_id)
        .options(selectinload(TimelineMarker.author))
        .order_by(TimelineMarker.timestamp_seconds.asc())
    )
    if media_id:
        stmt = stmt.where(TimelineMarker.media_id == media_id)
    if marker_type:
        stmt = stmt.where(TimelineMarker.marker_type == marker_type)
    if expert_only:
        stmt = stmt.where(TimelineMarker.is_expert == True)

    result = await db.execute(stmt)
    markers = result.scalars().all()
    return [_serialize(m) for m in markers]


@router.post(
    "/{case_id}/timeline",
    response_model=TimelineMarkerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_timeline_marker(
    case_id: UUID,
    body: TimelineMarkerCreate,
    db: DB,
    user: CurrentUser,
):
    """
    Add a timeline marker to a case.

    Marks a specific moment in a video as a named behavioral event.
    """
    # Verify case exists
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    if case_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    if body.marker_type not in MARKER_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "detail": f"Invalid marker_type. Valid: {sorted(MARKER_TYPES)}",
                "code": "validation_error",
            },
        )

    # Validate media_id if provided
    if body.media_id:
        media_result = await db.execute(
            select(CaseMedia).where(
                CaseMedia.id == body.media_id,
                CaseMedia.case_id == case_id,
            )
        )
        if media_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Media not found on this case", "code": "not_found"},
            )

    marker = TimelineMarker(
        case_id=case_id,
        media_id=body.media_id,
        author_id=user.id,
        timestamp_seconds=body.timestamp_seconds,
        label=body.label,
        marker_type=body.marker_type,
        notes=body.notes,
        is_expert=user.role in ("expert", "admin"),
    )
    db.add(marker)
    await db.flush()

    # Load author for response
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(TimelineMarker)
        .where(TimelineMarker.id == marker.id)
        .options(selectinload(TimelineMarker.author))
    )
    marker = result.scalar_one()
    log.info(
        "Timeline marker added: case=%s ts=%.1fs type=%s by %s",
        case_id,
        body.timestamp_seconds,
        body.marker_type,
        user.username,
    )
    return _serialize(marker)


@router.patch("/{case_id}/timeline/{marker_id}", response_model=TimelineMarkerResponse)
async def update_timeline_marker(
    case_id: UUID,
    marker_id: UUID,
    body: TimelineMarkerPatch,
    db: DB,
    user: CurrentUser,
):
    """Update a timeline marker. Author or admin only."""
    result = await db.execute(
        select(TimelineMarker)
        .where(TimelineMarker.id == marker_id, TimelineMarker.case_id == case_id)
        .options(selectinload(TimelineMarker.author))
    )
    marker = result.scalar_one_or_none()
    if marker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Timeline marker not found", "code": "not_found"},
        )
    if marker.author_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Not authorized to edit this marker", "code": "forbidden"},
        )
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(marker, field, value)
    return _serialize(marker)


@router.delete(
    "/{case_id}/timeline/{marker_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_timeline_marker(
    case_id: UUID,
    marker_id: UUID,
    db: DB,
    user: CurrentUser,
):
    """Delete a timeline marker. Author or admin only."""
    result = await db.execute(
        select(TimelineMarker).where(
            TimelineMarker.id == marker_id,
            TimelineMarker.case_id == case_id,
        )
    )
    marker = result.scalar_one_or_none()
    if marker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Timeline marker not found", "code": "not_found"},
        )
    if marker.author_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Not authorized", "code": "forbidden"},
        )
    await db.delete(marker)
