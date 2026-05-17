"""
Dataset governance routes — snapshots, provenance, and lineage.

Dataset snapshots provide:
- Point-in-time metadata capture
- Dataset version tracking for citations
- Foundation for training dataset release management

Annotation lineage provides:
- Full provenance chain for any annotation
- Evidence of expert credentialing at annotation time
- Taxonomy references used
- Revision history
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.dataset_snapshot import DatasetSnapshot
from app.services.analytics_service import platform_metrics
from app.services.event_publisher import dataset_snapshot_created, publish

log = logging.getLogger("barkmind.dataset")
router = APIRouter(prefix="/dataset", tags=["dataset"])


@router.post("/snapshot", status_code=status.HTTP_201_CREATED)
async def create_snapshot(
    db: DB,
    user: CurrentUser,
    name: str = "snapshot",
    description: str | None = None,
    version_tag: str | None = None,
):
    """
    Create a named dataset snapshot capturing current platform statistics.

    A snapshot is a versioned metadata record — it captures the counts and
    distribution of data at a specific moment. It does NOT contain the full data
    (use exports for that).
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    # Gather comprehensive stats for snapshot
    metrics = await platform_metrics(db)

    from app.services.analytics_service import (
        annotation_analytics,
        case_analytics,
        consensus_analytics,
        taxonomy_analytics,
    )

    cases = await case_analytics(db)
    annotations = await annotation_analytics(db)
    taxonomies = await taxonomy_analytics(db)
    consensus = await consensus_analytics(db)

    snapshot_meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform_version": "1.0.0",
        **metrics["totals"],
        "status_distribution": cases["status_distribution"],
        "setting_distribution": cases["setting_distribution"],
        "annotation_type_distribution": annotations["type_distribution"],
        "taxonomy_category_usage": taxonomies["category_usage"],
        "consensus_agreement_rate": consensus["agreement_rate_pct"],
        "top_taxonomy_terms": annotations["top_taxonomy_terms"][:20],
    }

    case_count = metrics["totals"]["cases"]
    annotation_count = metrics["totals"]["annotations"]
    expert_count = metrics["totals"].get("expert_count", 0)

    # Get expert count properly
    from app.models.user import User
    from sqlalchemy import func
    expert_count = await db.scalar(
        select(func.count(User.id)).where(
            User.role.in_(["expert", "admin"]), User.is_active == True
        )
    ) or 0

    snapshot = DatasetSnapshot(
        name=name,
        description=description,
        created_by=user.id,
        version_tag=version_tag or datetime.now(timezone.utc).strftime("%Y%m%d"),
        case_count=case_count,
        annotation_count=annotation_count,
        expert_count=expert_count,
        snapshot_metadata=snapshot_meta,
    )
    db.add(snapshot)
    await db.flush()

    await publish(
        db,
        dataset_snapshot_created(user.id, snapshot.id, name, case_count),
    )

    log.info("Dataset snapshot created: %s (%d cases) by %s", name, case_count, user.username)

    return {
        "id": str(snapshot.id),
        "name": snapshot.name,
        "version_tag": snapshot.version_tag,
        "case_count": snapshot.case_count,
        "annotation_count": snapshot.annotation_count,
        "expert_count": snapshot.expert_count,
        "created_at": snapshot.created_at.isoformat(),
        "snapshot_metadata": snapshot.snapshot_metadata,
    }


@router.get("/snapshots")
async def list_snapshots(db: DB, user: CurrentUser):
    """List all dataset snapshots (admin only)."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    result = await db.execute(
        select(DatasetSnapshot)
        .options(selectinload(DatasetSnapshot.creator))
        .order_by(DatasetSnapshot.created_at.desc())
    )
    snapshots = result.scalars().all()

    return [
        {
            "id": str(s.id),
            "name": s.name,
            "description": s.description,
            "version_tag": s.version_tag,
            "case_count": s.case_count,
            "annotation_count": s.annotation_count,
            "expert_count": s.expert_count,
            "created_by": s.creator.username,
            "created_at": s.created_at.isoformat(),
        }
        for s in snapshots
    ]


@router.get("/snapshots/{snapshot_id}")
async def get_snapshot(snapshot_id: UUID, db: DB, user: CurrentUser):
    """Get snapshot metadata including full stats (admin only)."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    result = await db.execute(
        select(DatasetSnapshot)
        .where(DatasetSnapshot.id == snapshot_id)
        .options(selectinload(DatasetSnapshot.creator))
    )
    snapshot = result.scalar_one_or_none()
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Snapshot not found", "code": "not_found"},
        )

    return {
        "id": str(snapshot.id),
        "name": snapshot.name,
        "description": snapshot.description,
        "version_tag": snapshot.version_tag,
        "case_count": snapshot.case_count,
        "annotation_count": snapshot.annotation_count,
        "expert_count": snapshot.expert_count,
        "created_by": snapshot.creator.username,
        "created_at": snapshot.created_at.isoformat(),
        "snapshot_metadata": snapshot.snapshot_metadata,
    }


@router.get("/lineage/{case_id}")
async def get_annotation_lineage(case_id: UUID, db: DB, user: CurrentUser):
    """
    Get complete annotation provenance chain for a case.

    Returns:
    - All annotations with revision history
    - Author credentials at annotation time
    - Taxonomy terms referenced
    - Timeline of changes

    This is the evidence chain for the behavioral intelligence dataset.
    """
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    from app.models.annotation import Annotation
    from app.models.annotation_revision import AnnotationRevision
    from app.models.annotation_taxonomy_ref import AnnotationTaxonomyRef
    from app.models.case import Case
    from app.models.expert_profile import ExpertProfile

    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    case = case_result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    ann_result = await db.execute(
        select(Annotation)
        .where(Annotation.case_id == case_id)
        .options(
            selectinload(Annotation.author),
            selectinload(Annotation.taxonomy_refs).selectinload(AnnotationTaxonomyRef.term),
            selectinload(Annotation.revisions).selectinload(AnnotationRevision.editor),
        )
        .order_by(Annotation.created_at.asc())
    )
    annotations = ann_result.scalars().all()

    lineage = []
    for a in annotations:
        # Get author's expert profile at annotation time
        ep_result = await db.execute(
            select(ExpertProfile).where(ExpertProfile.user_id == a.author_id)
        )
        ep = ep_result.scalar_one_or_none()

        lineage.append({
            "annotation_id": str(a.id),
            "annotation_type": a.annotation_type,
            "body": a.body,
            "confidence_level": a.confidence_level,
            "is_expert": a.is_expert,
            "timestamp_range": (
                [a.timestamp_start, a.timestamp_end]
                if a.timestamp_start is not None else None
            ),
            "author": {
                "username": a.author.username,
                "role": a.author.role,
                "verification_status": ep.verification_status if ep else None,
                "display_title": ep.display_title if ep else None,
            },
            "taxonomy_terms": [
                {"slug": ref.term.slug, "label": ref.term.label, "category": ref.term.category}
                for ref in a.taxonomy_refs
            ],
            "revision_count": len(a.revisions),
            "revisions": [
                {
                    "editor": r.editor.username,
                    "change_reason": r.change_reason,
                    "previous_body": r.previous_body,
                    "previous_confidence": r.previous_confidence_level,
                    "revised_at": r.created_at.isoformat(),
                }
                for r in a.revisions
            ],
            "created_at": a.created_at.isoformat(),
            "last_updated_at": a.updated_at.isoformat(),
        })

    return {
        "case_id": str(case_id),
        "case_title": case.title,
        "annotation_count": len(lineage),
        "lineage": lineage,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
