"""
Governance operations routes — Aegis-compatible status and metrics endpoints.

These endpoints are designed to be polled by Aegis for:
- Platform health and compliance scoring
- Runtime capability declarations
- Live governance metrics

Also includes organization management (multi-tenant foundation).
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.deps import CurrentUser, DB
from app.models.annotation import Annotation
from app.models.audit_event import AuditEvent
from app.models.case import Case
from app.models.evidence_lock import EvidenceLock
from app.models.expert_profile import ExpertProfile
from app.models.organization import Organization
from app.models.review_assignment import ReviewAssignment
from app.models.user import User
from app.services.analytics_service import platform_metrics

log = logging.getLogger("barkmind.governance_ops")
router = APIRouter(tags=["governance"])


@router.get("/governance/status")
async def governance_status(db: DB):
    """
    Comprehensive governance health check.

    Consumed by Aegis for compliance scoring and topology reconciliation.
    Returns platform status, compliance indicators, and runtime capabilities.
    No auth required — Aegis polls this endpoint without a user token.
    """
    now = datetime.now(timezone.utc)

    total_cases = await db.scalar(select(func.count(Case.id)).where(Case.is_archived == False)) or 0
    locked_cases = await db.scalar(select(func.count(EvidenceLock.id))) or 0
    pending_reviews = await db.scalar(
        select(func.count(ReviewAssignment.id)).where(
            ReviewAssignment.status.in_(["pending", "claimed"])
        )
    ) or 0
    verified_experts = await db.scalar(
        select(func.count(ExpertProfile.id)).where(
            ExpertProfile.verification_status == "verified"
        )
    ) or 0
    recent_events = await db.scalar(
        select(func.count(AuditEvent.id)).where(
            AuditEvent.created_at >= now.replace(hour=0, minute=0, second=0)
        )
    ) or 0

    return {
        "platform": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "timestamp": now.isoformat(),
        "governance": {
            "doctrine_version": settings.doctrine_version,
            "audit_trail": True,
            "evidence_locking": True,
            "expert_verification": True,
            "consensus_system": True,
            "reputation_tracking": True,
            "export_traceability": True,
        },
        "metrics": {
            "total_cases": total_cases,
            "locked_cases": locked_cases,
            "pending_reviews": pending_reviews,
            "verified_experts": verified_experts,
            "audit_events_today": recent_events,
        },
        "compliance": {
            "health_endpoint": True,
            "whoami_endpoint": True,
            "aegis_meta_endpoint": True,
            "version_endpoint": True,
            "lifecycle_scripts": True,
            "port_conflict_detection": True,
            "topology_registered": True,
        },
        "capabilities": [
            "behavioral_annotation",
            "expert_review",
            "multi_expert_consensus",
            "evidence_locking",
            "audit_trail",
            "dataset_export",
            "telemetry",
            "reputation_system",
            "taxonomy_management",
            "timeline_markers",
        ],
    }


@router.get("/governance/metrics")
async def governance_metrics(db: DB):
    """
    Quantitative platform metrics for Aegis dashboard.

    Returns structured numeric metrics consumed by Aegis governance scoring.
    No auth required.
    """
    metrics = await platform_metrics(db)
    return {
        **metrics,
        "platform": settings.app_name,
        "backend_port": settings.backend_port,
        "frontend_port": settings.frontend_port,
    }


# ─── Organizations (Multi-tenant foundation) ──────────────────────────────────

org_router = APIRouter(prefix="/organizations", tags=["organizations"])


@org_router.get("")
async def list_organizations(db: DB, user: CurrentUser):
    """Admin: list all organizations."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    result = await db.execute(
        select(Organization).order_by(Organization.name.asc())
    )
    orgs = result.scalars().all()

    return [
        {
            "id": str(o.id),
            "name": o.name,
            "slug": o.slug,
            "description": o.description,
            "created_at": o.created_at.isoformat(),
        }
        for o in orgs
    ]


@org_router.post("", status_code=status.HTTP_201_CREATED)
async def create_organization(
    db: DB,
    user: CurrentUser,
    name: str,
    slug: str,
    description: str | None = None,
):
    """Admin: create an organization."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    existing = await db.execute(select(Organization).where(Organization.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": f"Slug '{slug}' already exists", "code": "conflict"},
        )

    org = Organization(name=name, slug=slug, description=description)
    db.add(org)
    await db.flush()

    log.info("Organization created: %s by %s", slug, user.username)
    return {"id": str(org.id), "name": org.name, "slug": org.slug}


@org_router.patch("/{org_id}/assign/{username}")
async def assign_user_to_org(
    org_id: str,
    username: str,
    db: DB,
    user: CurrentUser,
):
    """Admin: assign a user to an organization."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    import uuid
    try:
        org_uuid = uuid.UUID(org_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"detail": "Invalid org_id", "code": "validation_error"})

    org_result = await db.execute(select(Organization).where(Organization.id == org_uuid))
    org = org_result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail={"detail": "Organization not found", "code": "not_found"})

    user_result = await db.execute(select(User).where(User.username == username, User.is_active == True))
    target = user_result.scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail={"detail": "User not found", "code": "not_found"})

    target.organization_id = org_uuid
    log.info("User %s assigned to org %s", username, org.slug)
    return {"username": username, "organization": org.slug}
