"""
Analytics service — aggregate platform intelligence queries.

All queries are read-only SQL aggregations. No AI decisions.
Results are structured data for dashboards and operational monitoring.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.annotation import Annotation
from app.models.annotation_taxonomy_ref import AnnotationTaxonomyRef
from app.models.audit_event import AuditEvent
from app.models.case import Case
from app.models.case_media import CaseMedia
from app.models.case_tag import CaseTag
from app.models.consensus import ConsensusRecord, ExpertOpinion
from app.models.evidence_lock import EvidenceLock
from app.models.expert_profile import ExpertProfile
from app.models.resolution import ExpertResolution
from app.models.review_assignment import ReviewAssignment
from app.models.taxonomy import TaxonomyTerm
from app.models.timeline_marker import TimelineMarker
from app.models.user import User

log = logging.getLogger("barkmind.analytics")


async def case_analytics(db: AsyncSession) -> dict:
    """Case velocity, status distribution, setting distribution."""
    # Status distribution
    status_result = await db.execute(
        select(Case.status, func.count(Case.id).label("count"))
        .where(Case.is_archived == False)
        .group_by(Case.status)
        .order_by(Case.status)
    )
    status_dist = {row.status: row.count for row in status_result.fetchall()}

    # Setting distribution
    setting_result = await db.execute(
        select(Case.setting, func.count(Case.id).label("count"))
        .where(Case.is_archived == False, Case.setting.isnot(None))
        .group_by(Case.setting)
        .order_by(func.count(Case.id).desc())
    )
    setting_dist = {row.setting: row.count for row in setting_result.fetchall()}

    # Total counts
    total = await db.scalar(select(func.count(Case.id)).where(Case.is_archived == False)) or 0
    locked = await db.scalar(select(func.count(Case.id)).where(Case.status == "locked")) or 0
    resolved = await db.scalar(
        select(func.count(Case.id)).where(Case.status.in_(["resolved", "locked"]))
    ) or 0

    # Last 7 days vs previous 7 days (velocity)
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    recent_7 = await db.scalar(
        select(func.count(Case.id)).where(Case.created_at >= week_ago)
    ) or 0
    prior_7 = await db.scalar(
        select(func.count(Case.id)).where(
            Case.created_at >= two_weeks_ago, Case.created_at < week_ago
        )
    ) or 0

    # Median resolution time: time from created_at to locked_at
    # Computed via avg for simplicity
    avg_resolution = await db.scalar(
        select(
            func.avg(
                func.extract("epoch", EvidenceLock.locked_at) -
                func.extract("epoch", Case.created_at)
            )
        )
        .select_from(EvidenceLock)
        .join(Case, Case.id == EvidenceLock.case_id)
    )

    return {
        "total_cases": total,
        "resolved_or_locked": resolved,
        "locked": locked,
        "resolution_rate_pct": round((resolved / total * 100) if total > 0 else 0, 1),
        "status_distribution": status_dist,
        "setting_distribution": setting_dist,
        "velocity_last_7_days": recent_7,
        "velocity_prior_7_days": prior_7,
        "velocity_change_pct": round(
            ((recent_7 - prior_7) / prior_7 * 100) if prior_7 > 0 else 0, 1
        ),
        "avg_resolution_hours": round(avg_resolution / 3600, 1) if avg_resolution else None,
    }


async def annotation_analytics(db: AsyncSession) -> dict:
    """Annotation volume, type distribution, taxonomy adoption."""
    total = await db.scalar(select(func.count(Annotation.id))) or 0
    expert_count = await db.scalar(
        select(func.count(Annotation.id)).where(Annotation.is_expert == True)
    ) or 0
    with_taxonomy = await db.scalar(
        select(func.count(func.distinct(AnnotationTaxonomyRef.annotation_id)))
    ) or 0
    with_confidence = await db.scalar(
        select(func.count(Annotation.id)).where(Annotation.confidence_level.isnot(None))
    ) or 0
    with_timestamp = await db.scalar(
        select(func.count(Annotation.id)).where(Annotation.timestamp_start.isnot(None))
    ) or 0

    # Type distribution
    type_result = await db.execute(
        select(Annotation.annotation_type, func.count(Annotation.id).label("count"))
        .group_by(Annotation.annotation_type)
        .order_by(func.count(Annotation.id).desc())
    )
    type_dist = {row.annotation_type: row.count for row in type_result.fetchall()}

    # Confidence distribution
    conf_result = await db.execute(
        select(Annotation.confidence_level, func.count(Annotation.id).label("count"))
        .where(Annotation.confidence_level.isnot(None))
        .group_by(Annotation.confidence_level)
    )
    conf_dist = {row.confidence_level: row.count for row in conf_result.fetchall()}

    # Top taxonomy terms by annotation reference count
    top_terms_result = await db.execute(
        select(
            TaxonomyTerm.slug,
            TaxonomyTerm.label,
            TaxonomyTerm.category,
            func.count(AnnotationTaxonomyRef.id).label("usage_count"),
        )
        .join(TaxonomyTerm, TaxonomyTerm.id == AnnotationTaxonomyRef.taxonomy_term_id)
        .group_by(TaxonomyTerm.id, TaxonomyTerm.slug, TaxonomyTerm.label, TaxonomyTerm.category)
        .order_by(func.count(AnnotationTaxonomyRef.id).desc())
        .limit(15)
    )
    top_terms = [
        {"slug": r.slug, "label": r.label, "category": r.category, "count": r.usage_count}
        for r in top_terms_result.fetchall()
    ]

    # Total case count for avg calculation
    total_cases = await db.scalar(select(func.count(Case.id)).where(Case.is_archived == False)) or 1

    return {
        "total_annotations": total,
        "expert_annotations": expert_count,
        "community_annotations": total - expert_count,
        "expert_pct": round((expert_count / total * 100) if total > 0 else 0, 1),
        "with_taxonomy_refs": with_taxonomy,
        "taxonomy_adoption_pct": round((with_taxonomy / total * 100) if total > 0 else 0, 1),
        "with_confidence": with_confidence,
        "with_timestamp_range": with_timestamp,
        "avg_annotations_per_case": round(total / total_cases, 2),
        "type_distribution": type_dist,
        "confidence_distribution": conf_dist,
        "top_taxonomy_terms": top_terms,
    }


async def expert_analytics(db: AsyncSession) -> dict:
    """Expert participation, review throughput, reputation distribution."""
    total_experts = await db.scalar(
        select(func.count(User.id)).where(
            User.role.in_(["expert", "admin"]), User.is_active == True
        )
    ) or 0

    verified_experts = await db.scalar(
        select(func.count(ExpertProfile.id)).where(
            ExpertProfile.verification_status == "verified"
        )
    ) or 0

    total_resolutions = await db.scalar(select(func.count(ExpertResolution.id))) or 0
    total_assignments = await db.scalar(select(func.count(ReviewAssignment.id))) or 0
    completed_assignments = await db.scalar(
        select(func.count(ReviewAssignment.id)).where(
            ReviewAssignment.status == "complete"
        )
    ) or 0
    pending_assignments = await db.scalar(
        select(func.count(ReviewAssignment.id)).where(
            ReviewAssignment.status.in_(["pending", "claimed"])
        )
    ) or 0

    # Stale assignments: pending for > 7 days
    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    stale_assignments = await db.scalar(
        select(func.count(ReviewAssignment.id)).where(
            ReviewAssignment.status == "pending",
            ReviewAssignment.created_at < stale_cutoff,
        )
    ) or 0

    # Top experts by review count
    top_experts_result = await db.execute(
        select(
            User.username,
            User.reputation_score,
            ExpertProfile.review_count,
            ExpertProfile.verification_status,
        )
        .join(ExpertProfile, ExpertProfile.user_id == User.id)
        .order_by(ExpertProfile.review_count.desc())
        .limit(10)
    )
    top_experts = [
        {
            "username": r.username,
            "reputation_score": r.reputation_score,
            "review_count": r.review_count,
            "verified": r.verification_status == "verified",
        }
        for r in top_experts_result.fetchall()
    ]

    # Avg time to claim (hours)
    avg_claim_time = await db.scalar(
        select(
            func.avg(
                func.extract("epoch", ReviewAssignment.claimed_at) -
                func.extract("epoch", ReviewAssignment.created_at)
            )
        ).where(ReviewAssignment.claimed_at.isnot(None))
    )

    return {
        "total_experts": total_experts,
        "verified_experts": verified_experts,
        "total_resolutions": total_resolutions,
        "total_assignments": total_assignments,
        "completed_assignments": completed_assignments,
        "pending_assignments": pending_assignments,
        "stale_assignments_7d": stale_assignments,
        "avg_time_to_claim_hours": round(avg_claim_time / 3600, 1) if avg_claim_time else None,
        "top_experts": top_experts,
    }


async def taxonomy_analytics(db: AsyncSession) -> dict:
    """Taxonomy term adoption and category usage."""
    total_terms = await db.scalar(select(func.count(TaxonomyTerm.id))) or 0
    active_terms = await db.scalar(
        select(func.count(TaxonomyTerm.id)).where(TaxonomyTerm.is_active == True)
    ) or 0

    # Category usage (by annotation taxonomy refs)
    cat_result = await db.execute(
        select(
            TaxonomyTerm.category,
            func.count(AnnotationTaxonomyRef.id).label("ref_count"),
        )
        .join(TaxonomyTerm, TaxonomyTerm.id == AnnotationTaxonomyRef.taxonomy_term_id)
        .group_by(TaxonomyTerm.category)
        .order_by(func.count(AnnotationTaxonomyRef.id).desc())
    )
    cat_usage = {r.category: r.ref_count for r in cat_result.fetchall()}

    # Terms with zero annotation refs (unused)
    unused_result = await db.execute(
        select(TaxonomyTerm.slug, TaxonomyTerm.label, TaxonomyTerm.category)
        .where(
            TaxonomyTerm.is_active == True,
            ~TaxonomyTerm.slug.in_(
                select(TaxonomyTerm.slug)
                .join(AnnotationTaxonomyRef, AnnotationTaxonomyRef.taxonomy_term_id == TaxonomyTerm.id)
                .scalar_subquery()
                .correlate(None)
            )
        )
        .limit(20)
    )
    unused_terms = [{"slug": r.slug, "label": r.label, "category": r.category} for r in unused_result.fetchall()]

    # Also check case_tags for tag usage
    tag_usage_result = await db.execute(
        select(
            CaseTag.tag_id,
            func.count(CaseTag.id).label("usage_count"),
        )
        .group_by(CaseTag.tag_id)
        .order_by(func.count(CaseTag.id).desc())
        .limit(10)
    )

    return {
        "total_terms": total_terms,
        "active_terms": active_terms,
        "total_category_refs": sum(cat_usage.values()),
        "category_usage": cat_usage,
        "unused_terms": unused_terms,
        "unused_term_count": len(unused_terms),
    }


async def consensus_analytics(db: AsyncSession) -> dict:
    """Consensus system participation and agreement rates."""
    total = await db.scalar(select(func.count(ConsensusRecord.id))) or 0
    reached = await db.scalar(
        select(func.count(ConsensusRecord.id)).where(ConsensusRecord.status == "reached")
    ) or 0
    disputed = await db.scalar(
        select(func.count(ConsensusRecord.id)).where(ConsensusRecord.status == "disputed")
    ) or 0
    escalated = await db.scalar(
        select(func.count(ConsensusRecord.id)).where(ConsensusRecord.status == "escalated")
    ) or 0
    open_count = await db.scalar(
        select(func.count(ConsensusRecord.id)).where(ConsensusRecord.status == "open")
    ) or 0

    total_opinions = await db.scalar(select(func.count(ExpertOpinion.id))) or 0
    avg_opinions = round(total_opinions / total, 2) if total > 0 else 0

    # Consensus verdict distribution
    verdict_result = await db.execute(
        select(ConsensusRecord.consensus_verdict, func.count(ConsensusRecord.id).label("count"))
        .where(ConsensusRecord.consensus_verdict.isnot(None))
        .group_by(ConsensusRecord.consensus_verdict)
        .order_by(func.count(ConsensusRecord.id).desc())
    )
    verdict_dist = {r.consensus_verdict: r.count for r in verdict_result.fetchall()}

    return {
        "total_consensus_reviews": total,
        "reached": reached,
        "disputed": disputed,
        "escalated": escalated,
        "open": open_count,
        "agreement_rate_pct": round((reached / total * 100) if total > 0 else 0, 1),
        "dispute_rate_pct": round((disputed / total * 100) if total > 0 else 0, 1),
        "total_opinions": total_opinions,
        "avg_opinions_per_consensus": avg_opinions,
        "verdict_distribution": verdict_dist,
    }


async def platform_metrics(db: AsyncSession) -> dict:
    """Comprehensive platform metrics for Aegis and governance dashboards."""
    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(hours=24)
    week_ago = now - timedelta(days=7)

    # Active users in last 24h (distinct actors in audit_events)
    active_24h = await db.scalar(
        select(func.count(func.distinct(AuditEvent.actor_id))).where(
            AuditEvent.created_at >= day_ago,
            AuditEvent.actor_id.isnot(None),
        )
    ) or 0

    # Event volume in last 7 days
    event_volume_7d = await db.scalar(
        select(func.count(AuditEvent.id)).where(AuditEvent.created_at >= week_ago)
    ) or 0

    # Event type distribution (last 7 days)
    event_types_result = await db.execute(
        select(AuditEvent.event_type, func.count(AuditEvent.id).label("count"))
        .where(AuditEvent.created_at >= week_ago)
        .group_by(AuditEvent.event_type)
        .order_by(func.count(AuditEvent.id).desc())
        .limit(10)
    )
    event_types = {r.event_type: r.count for r in event_types_result.fetchall()}

    # Core counts
    total_cases = await db.scalar(select(func.count(Case.id)).where(Case.is_archived == False)) or 0
    total_users = await db.scalar(select(func.count(User.id)).where(User.is_active == True)) or 0
    total_annotations = await db.scalar(select(func.count(Annotation.id))) or 0
    total_media = await db.scalar(select(func.count(CaseMedia.id))) or 0
    total_exports = await db.scalar(
        select(func.count(
            __import__("app.models.export_job", fromlist=["ExportJob"]).ExportJob.id
        ))
    ) or 0
    pending_reviews = await db.scalar(
        select(func.count(ReviewAssignment.id)).where(
            ReviewAssignment.status.in_(["pending", "claimed"])
        )
    ) or 0
    locked_cases = await db.scalar(
        select(func.count(EvidenceLock.id))
    ) or 0

    return {
        "platform": "barkmind",
        "generated_at": now.isoformat(),
        "totals": {
            "cases": total_cases,
            "users": total_users,
            "annotations": total_annotations,
            "media_files": total_media,
            "exports": total_exports,
            "locked_cases": locked_cases,
            "pending_reviews": pending_reviews,
        },
        "activity": {
            "active_users_24h": active_24h,
            "events_last_7d": event_volume_7d,
            "top_event_types_7d": event_types,
        },
    }


async def detect_stale_reviews(db: AsyncSession, days: int = 7) -> list[dict]:
    """Find review assignments pending for more than N days without activity."""
    stale_cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = await db.execute(
        select(
            ReviewAssignment,
        )
        .where(
            ReviewAssignment.status.in_(["pending", "claimed"]),
            ReviewAssignment.created_at < stale_cutoff,
        )
        .order_by(ReviewAssignment.created_at.asc())
        .limit(50)
    )
    assignments = result.scalars().all()

    stale = []
    for a in assignments:
        age_days = (datetime.now(timezone.utc) - a.created_at).days
        stale.append({
            "assignment_id": str(a.id),
            "case_id": str(a.case_id),
            "status": a.status,
            "review_type": a.review_type,
            "days_pending": age_days,
            "created_at": a.created_at.isoformat(),
        })

    return stale
