"""
Audit log and governance dashboard routes.

Audit events are immutable records of governance actions.
Only admin can read the full audit log.
Case-level audit is visible to experts reviewing that case.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.audit_event import AuditEvent
from app.models.case import Case
from app.models.reputation_event import ReputationEvent
from app.models.review_assignment import ReviewAssignment
from app.models.user import User

log = logging.getLogger("barkmind.audit")
router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit_events(
    db: DB,
    user: CurrentUser,
    event_type: str | None = Query(None),
    target_type: str | None = Query(None),
    target_id: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Admin: list audit events with optional filtering."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    stmt = (
        select(AuditEvent)
        .options(selectinload(AuditEvent.actor))
        .order_by(AuditEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    if target_type:
        stmt = stmt.where(AuditEvent.target_type == target_type)
    if target_id:
        stmt = stmt.where(AuditEvent.target_id == target_id)

    result = await db.execute(stmt)
    events = result.scalars().all()

    total_result = await db.scalar(select(func.count(AuditEvent.id)))

    return {
        "total": total_result,
        "offset": offset,
        "limit": limit,
        "events": [_serialize_event(e) for e in events],
    }


@router.get("/cases/{case_id}")
async def get_case_audit(case_id: UUID, db: DB, user: CurrentUser):
    """Expert/admin: get all audit events for a specific case."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    result = await db.execute(
        select(AuditEvent)
        .where(
            AuditEvent.target_type == "case",
            AuditEvent.target_id == case_id,
        )
        .options(selectinload(AuditEvent.actor))
        .order_by(AuditEvent.created_at.asc())
    )
    events = result.scalars().all()
    return [_serialize_event(e) for e in events]


@router.get("/governance/summary")
async def get_governance_summary(db: DB, user: CurrentUser):
    """Admin: platform governance overview."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    # Case status distribution
    from sqlalchemy import literal_column
    status_result = await db.execute(
        select(Case.status, func.count(Case.id).label("count"))
        .where(Case.is_archived == False)
        .group_by(Case.status)
        .order_by(Case.status)
    )
    status_dist = {row.status: row.count for row in status_result.fetchall()}

    # Expert count
    expert_count = await db.scalar(
        select(func.count(User.id)).where(
            User.role.in_(["expert", "admin"]),
            User.is_active == True,
        )
    ) or 0

    # Total cases
    total_cases = await db.scalar(
        select(func.count(Case.id)).where(Case.is_archived == False)
    ) or 0

    # Total annotations
    from app.models.annotation import Annotation
    total_annotations = await db.scalar(select(func.count(Annotation.id))) or 0

    # Recent audit events (last 10)
    recent_result = await db.execute(
        select(AuditEvent)
        .options(selectinload(AuditEvent.actor))
        .order_by(AuditEvent.created_at.desc())
        .limit(10)
    )
    recent_events = recent_result.scalars().all()

    # Pending assignments
    pending_assignments = await db.scalar(
        select(func.count(ReviewAssignment.id)).where(
            ReviewAssignment.status == "pending"
        )
    ) or 0

    return {
        "case_status_distribution": status_dist,
        "total_cases": total_cases,
        "total_annotations": total_annotations,
        "expert_count": expert_count,
        "pending_assignments": pending_assignments,
        "recent_audit_events": [_serialize_event(e) for e in recent_events],
    }


@router.get("/reputation/{username}")
async def get_reputation_history(username: str, db: DB, user: CurrentUser):
    """Get reputation event history for a user (own history or admin)."""
    target_result = await db.execute(
        select(User).where(User.username == username, User.is_active == True)
    )
    target = target_result.scalar_one_or_none()
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "User not found", "code": "not_found"},
        )

    if user.role != "admin" and user.id != target.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Can only view own reputation history", "code": "forbidden"},
        )

    result = await db.execute(
        select(ReputationEvent)
        .where(ReputationEvent.user_id == target.id)
        .order_by(ReputationEvent.created_at.desc())
        .limit(100)
    )
    events = result.scalars().all()

    return {
        "username": username,
        "current_score": target.reputation_score,
        "events": [
            {
                "id": str(e.id),
                "event_type": e.event_type,
                "delta": e.delta,
                "reference_type": e.reference_type,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
    }


def _serialize_event(e: AuditEvent) -> dict:
    return {
        "id": str(e.id),
        "event_type": e.event_type,
        "actor": e.actor.username if e.actor else None,
        "target_type": e.target_type,
        "target_id": str(e.target_id) if e.target_id else None,
        "metadata": e.event_metadata,
        "created_at": e.created_at.isoformat(),
    }
