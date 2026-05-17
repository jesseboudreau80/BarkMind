"""
Export routes — data export in JSON, CSV, and NDJSON formats.

All exports are logged in export_jobs for audit traceability.
Every export request creates an immutable audit record.

Supported export types: cases, annotations, audit, experts, consensus
Supported formats: json, csv, ndjson
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.export_job import ExportJob
from app.services.export_service import generate_export

log = logging.getLogger("barkmind.exports")
router = APIRouter(prefix="/exports", tags=["exports"])

VALID_TYPES = {"cases", "annotations", "audit", "experts", "consensus"}
VALID_FORMATS = {"json", "csv", "ndjson"}

CONTENT_TYPES = {
    "json": "application/json",
    "csv": "text/csv",
    "ndjson": "application/x-ndjson",
}
EXTENSIONS = {
    "json": "json",
    "csv": "csv",
    "ndjson": "ndjson",
}


@router.post("/{export_type}")
async def create_export(
    export_type: str,
    db: DB,
    user: CurrentUser,
    fmt: str = Query("json", alias="format"),
):
    """
    Generate and download an export.

    Creates an export_job record for audit traceability, generates the export,
    and returns it as a downloadable file response.

    Supported types: cases, annotations, audit, experts, consensus
    Supported formats: json (default), csv, ndjson
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required for data exports", "code": "forbidden"},
        )

    if export_type not in VALID_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "detail": f"Invalid export type. Valid: {sorted(VALID_TYPES)}",
                "code": "validation_error",
            },
        )

    if fmt not in VALID_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "detail": f"Invalid format. Valid: {sorted(VALID_FORMATS)}",
                "code": "validation_error",
            },
        )

    log.info("Export requested: type=%s fmt=%s by=%s", export_type, fmt, user.username)

    content, record_count = await generate_export(db, export_type, fmt, user.id)

    filename = f"barkmind_{export_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.{EXTENSIONS[fmt]}"

    return Response(
        content=content,
        media_type=CONTENT_TYPES[fmt],
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Export-Count": str(record_count),
            "X-Export-Type": export_type,
        },
    )


@router.get("/history")
async def list_export_history(
    db: DB,
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=200),
):
    """Admin: list all prior export jobs for audit traceability."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    result = await db.execute(
        select(ExportJob)
        .options(selectinload(ExportJob.requester))
        .order_by(ExportJob.created_at.desc())
        .limit(limit)
    )
    jobs = result.scalars().all()

    return [
        {
            "id": str(j.id),
            "export_type": j.export_type,
            "format": j.format,
            "status": j.status,
            "requested_by": j.requester.username,
            "record_count": j.record_count,
            "parameters": j.parameters,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]
