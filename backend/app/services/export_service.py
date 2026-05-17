"""
Export service — data export in JSON, CSV, and NDJSON formats.

All exports are logged in export_jobs for audit traceability.
Exports are generated synchronously (streamed) for MVP.
Future: async job queue + S3 storage for large exports.

Export types:
  cases          — case metadata + resolution verdict
  annotations    — annotation records with taxonomy refs
  audit          — governance audit event log
  experts        — expert profile statistics
  consensus      — consensus records and opinions
  full_dataset   — combined behavioral intelligence dataset (NDJSON)
"""
from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

log = logging.getLogger("barkmind.exports")


async def _fetch_cases(db: AsyncSession) -> list[dict]:
    from app.models.case import Case
    from app.models.resolution import ExpertResolution
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Case)
        .where(Case.is_archived == False)
        .options(
            selectinload(Case.submitter),
            selectinload(Case.expert_resolution).selectinload(ExpertResolution.expert),
        )
        .order_by(Case.created_at.asc())
    )
    cases = result.scalars().all()

    rows = []
    for c in cases:
        row = {
            "id": str(c.id),
            "title": c.title,
            "status": c.status,
            "setting": c.setting,
            "subject_age_estimate": c.subject_age_estimate,
            "subject_breed_note": c.subject_breed_note,
            "trigger_context": c.trigger_context,
            "species_context": c.species_context,
            "submitter": c.submitter.username,
            "view_count": c.view_count,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        if c.expert_resolution:
            r = c.expert_resolution
            row["resolution"] = {
                "verdict": r.verdict,
                "confidence_level": r.confidence_level,
                "expert": r.expert.username,
                "summary": r.summary,
                "submitted_at": r.created_at.isoformat(),
            }
        else:
            row["resolution"] = None
        rows.append(row)

    return rows


async def _fetch_annotations(db: AsyncSession) -> list[dict]:
    from app.models.annotation import Annotation
    from app.models.annotation_taxonomy_ref import AnnotationTaxonomyRef

    result = await db.execute(
        select(Annotation)
        .options(
            selectinload(Annotation.author),
            selectinload(Annotation.taxonomy_refs).selectinload(
                AnnotationTaxonomyRef.term
            ),
        )
        .order_by(Annotation.created_at.asc())
    )
    annotations = result.scalars().all()

    return [
        {
            "id": str(a.id),
            "case_id": str(a.case_id),
            "author": a.author.username,
            "is_expert": a.is_expert,
            "annotation_type": a.annotation_type,
            "body": a.body,
            "confidence_level": a.confidence_level,
            "timestamp_start": a.timestamp_start,
            "timestamp_end": a.timestamp_end,
            "taxonomy_terms": [
                {"slug": ref.term.slug, "label": ref.term.label, "category": ref.term.category}
                for ref in a.taxonomy_refs
            ],
            "created_at": a.created_at.isoformat(),
        }
        for a in annotations
    ]


async def _fetch_audit(db: AsyncSession) -> list[dict]:
    from app.services.event_publisher import get_event_stream
    return await get_event_stream(db, limit=10000, offset=0)


async def _fetch_experts(db: AsyncSession) -> list[dict]:
    from app.models.expert_profile import ExpertProfile
    from app.models.user import User

    result = await db.execute(
        select(ExpertProfile)
        .options(selectinload(ExpertProfile.user))
        .order_by(ExpertProfile.review_count.desc())
    )
    profiles = result.scalars().all()

    return [
        {
            "username": p.user.username,
            "display_title": p.display_title,
            "organization": p.organization,
            "verification_status": p.verification_status,
            "years_experience": p.years_experience,
            "specializations": p.specializations or [],
            "certifications": p.certifications or [],
            "review_count": p.review_count,
            "annotation_count": p.annotation_count,
            "reputation_score": p.user.reputation_score,
            "created_at": p.created_at.isoformat(),
        }
        for p in profiles
    ]


async def _fetch_consensus(db: AsyncSession) -> list[dict]:
    from app.models.consensus import ConsensusRecord, ExpertOpinion

    result = await db.execute(
        select(ConsensusRecord)
        .options(
            selectinload(ConsensusRecord.initiator),
            selectinload(ConsensusRecord.opinions).selectinload(ExpertOpinion.expert),
        )
        .order_by(ConsensusRecord.created_at.asc())
    )
    records = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "case_id": str(r.case_id),
            "status": r.status,
            "initiated_by": r.initiator.username,
            "verdict_tally": r.verdict_tally,
            "consensus_verdict": r.consensus_verdict,
            "consensus_confidence": r.consensus_confidence,
            "opinion_count": len(r.opinions),
            "opinions": [
                {
                    "expert": op.expert.username,
                    "verdict": op.verdict,
                    "confidence_level": op.confidence_level,
                    "summary": op.summary,
                }
                for op in r.opinions
            ],
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]


_FETCHERS = {
    "cases": _fetch_cases,
    "annotations": _fetch_annotations,
    "audit": _fetch_audit,
    "experts": _fetch_experts,
    "consensus": _fetch_consensus,
}


async def generate_export(
    db: AsyncSession,
    export_type: str,
    fmt: str,
    requested_by: UUID,
) -> tuple[bytes, int]:
    """
    Generate export bytes and record the export job.

    Returns (content_bytes, record_count).
    Logs the export in export_jobs for audit traceability.
    """
    from datetime import timezone
    from app.models.export_job import ExportJob
    from app.services.event_publisher import publish, export_requested

    fetcher = _FETCHERS.get(export_type)
    if fetcher is None:
        raise ValueError(f"Unknown export type: {export_type}")

    # Create export job record (pending)
    job = ExportJob(
        requested_by=requested_by,
        export_type=export_type,
        format=fmt,
        status="generating",
        parameters={"export_type": export_type, "format": fmt},
    )
    db.add(job)
    await db.flush()

    try:
        data = await fetcher(db)
        record_count = len(data)

        if fmt == "json":
            content = json.dumps({"export_type": export_type, "records": data, "count": record_count}, indent=2).encode()
        elif fmt == "ndjson":
            lines = [json.dumps(row) for row in data]
            content = "\n".join(lines).encode()
        elif fmt == "csv":
            if not data:
                content = b""
            else:
                out = io.StringIO()
                writer = csv.DictWriter(out, fieldnames=list(data[0].keys()))
                writer.writeheader()
                for row in data:
                    # Flatten nested dicts for CSV
                    flat = {
                        k: json.dumps(v) if isinstance(v, (dict, list)) else v
                        for k, v in row.items()
                    }
                    writer.writerow(flat)
                content = out.getvalue().encode()
        else:
            raise ValueError(f"Unknown format: {fmt}")

        # Update job record
        job.status = "ready"
        job.record_count = record_count
        job.completed_at = datetime.now(timezone.utc)

        # Emit audit event
        await publish(db, export_requested(requested_by, job.id, export_type, fmt))

        log.info("Export %s/%s: %d records by user %s", export_type, fmt, record_count, requested_by)
        return content, record_count

    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        raise
