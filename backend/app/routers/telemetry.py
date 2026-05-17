"""
Telemetry routes — event stream and live operational metrics.

These endpoints are consumed by:
- Aegis governance platform (status polling)
- Admin governance dashboards
- Future: Prometheus/metrics scraping

Service-key auth allows Aegis to poll without a user JWT.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select

from app.config import settings
from app.deps import CurrentUser, DB
from app.models.audit_event import AuditEvent
from app.services.analytics_service import detect_stale_reviews, platform_metrics
from app.services.event_publisher import get_event_stream

log = logging.getLogger("barkmind.telemetry")
router = APIRouter(prefix="/telemetry", tags=["telemetry"])


def _require_admin_or_service_key(
    x_service_key: str | None = Header(None, alias="X-Service-Key"),
):
    """Allow access with either an admin JWT or a known service key."""
    if x_service_key and x_service_key == settings.service_api_key:
        return True
    return None  # Falls through to JWT check in route


@router.get("/events")
async def get_events(
    db: DB,
    user: CurrentUser,
    since: str | None = Query(None, description="ISO timestamp — replay from this point"),
    event_type: str | None = Query(None),
    target_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Event stream — paginated audit events with optional replay capability.

    Pass ?since=2026-05-17T00:00:00Z to replay events from a specific timestamp.
    Events are ordered newest-first by default.
    """
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    since_dt = None
    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail={"detail": "Invalid 'since' timestamp format. Use ISO 8601.", "code": "validation_error"},
            )

    events = await get_event_stream(
        db,
        since=since_dt,
        event_type=event_type,
        target_type=target_type,
        limit=limit,
        offset=offset,
    )

    return {
        "events": events,
        "count": len(events),
        "since": since,
        "limit": limit,
        "offset": offset,
    }


@router.get("/summary")
async def get_telemetry_summary(db: DB, user: CurrentUser):
    """Event volume summary by type over the last 7 days."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    from datetime import timedelta
    from sqlalchemy import func

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    result = await db.execute(
        select(AuditEvent.event_type, func.count(AuditEvent.id).label("count"))
        .where(AuditEvent.created_at >= week_ago)
        .group_by(AuditEvent.event_type)
        .order_by(func.count(AuditEvent.id).desc())
    )
    by_type = {row.event_type: row.count for row in result.fetchall()}

    total = sum(by_type.values())

    return {
        "period": "7d",
        "total_events": total,
        "by_type": by_type,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ops")
async def live_ops_overview(db: DB, user: CurrentUser):
    """
    Live operational overview — key platform health indicators.

    Shows what needs attention right now:
    - Stale reviews (>7 days pending)
    - Pending assignments
    - Open consensus reviews
    - Recent escalations
    """
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    from app.models.case import Case
    from app.models.consensus import ConsensusRecord
    from app.models.review_assignment import ReviewAssignment
    from sqlalchemy import func

    pending = await db.scalar(
        select(func.count(ReviewAssignment.id)).where(
            ReviewAssignment.status.in_(["pending", "claimed"])
        )
    ) or 0

    open_consensus = await db.scalar(
        select(func.count(ConsensusRecord.id)).where(ConsensusRecord.status == "open")
    ) or 0

    escalated = await db.scalar(
        select(func.count(Case.id)).where(Case.status == "escalated", Case.is_archived == False)
    ) or 0

    stale = await detect_stale_reviews(db, days=7)

    return {
        "pending_assignments": pending,
        "open_consensus_reviews": open_consensus,
        "escalated_cases": escalated,
        "stale_reviews_count": len(stale),
        "stale_reviews": stale[:10],  # Show first 10 for UI
        "attention_required": pending > 0 or escalated > 0 or len(stale) > 0,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
