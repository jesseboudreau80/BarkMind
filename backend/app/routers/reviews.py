"""
Review assignment and evidence lock routes.

Review assignments connect expert reviewers to cases.
Evidence locks freeze case state after resolution.
Case status transitions (Phase 5 extended states) live here too.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.case import Case
from app.models.evidence_lock import EvidenceLock
from app.models.review_assignment import ReviewAssignment
from app.models.user import User
from app.schemas.review import (
    ASSIGNMENT_STATUSES,
    REVIEW_TYPES,
    AssignmentCreate,
    AssignmentResponse,
    CaseStatusUpdate,
    EvidenceLockCreate,
    EvidenceLockResponse,
)
from app.services.governance import award_reputation, emit_audit_event
from app.services.review_workflow import (
    ALL_CASE_STATUSES,
    build_case_snapshot,
    can_transition,
    is_case_locked,
)

log = logging.getLogger("barkmind.reviews")
router = APIRouter(tags=["reviews"])


# ─── Case Status ──────────────────────────────────────────────────────────────

@router.patch("/cases/{case_id}/status")
async def update_case_status(
    case_id: UUID,
    body: CaseStatusUpdate,
    db: DB,
    user: CurrentUser,
):
    """
    Update case status using the Phase 5 extended state machine.

    Expert/admin can transition cases through review workflow states.
    """
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    if body.status not in ALL_CASE_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "detail": f"Invalid status. Valid: {sorted(ALL_CASE_STATUSES)}",
                "code": "validation_error",
            },
        )

    result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    if not can_transition(case.status, body.status, is_admin=user.role == "admin"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": f"Cannot transition from '{case.status}' to '{body.status}'",
                "code": "invalid_transition",
            },
        )

    old_status = case.status
    case.status = body.status

    await emit_audit_event(
        db, "case_status_changed", user.id, "case", case_id,
        {"from": old_status, "to": body.status, "reason": body.reason}
    )

    return {"case_id": str(case_id), "old_status": old_status, "new_status": body.status}


# ─── Review Assignments ───────────────────────────────────────────────────────

@router.get("/cases/{case_id}/assignments")
async def list_assignments(case_id: UUID, db: DB, user: CurrentUser):
    """List all review assignments for a case."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    result = await db.execute(
        select(ReviewAssignment)
        .where(ReviewAssignment.case_id == case_id)
        .options(
            selectinload(ReviewAssignment.reviewer),
            selectinload(ReviewAssignment.assigner),
        )
        .order_by(ReviewAssignment.created_at.desc())
    )
    assignments = result.scalars().all()
    return [_serialize_assignment(a) for a in assignments]


@router.post("/cases/{case_id}/assign", status_code=status.HTTP_201_CREATED)
async def assign_case(case_id: UUID, body: AssignmentCreate, db: DB, user: CurrentUser):
    """Admin/expert: assign a case to an expert for review."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    if case_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    reviewer_result = await db.execute(
        select(User).where(
            User.username == body.assigned_to_username,
            User.is_active == True,
        )
    )
    reviewer = reviewer_result.scalar_one_or_none()
    if reviewer is None or reviewer.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Reviewer not found or not an expert", "code": "not_found"},
        )

    if body.review_type not in REVIEW_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": f"Invalid review_type. Valid: {REVIEW_TYPES}", "code": "validation_error"},
        )

    assignment = ReviewAssignment(
        case_id=case_id,
        assigned_to=reviewer.id,
        assigned_by=user.id,
        status="pending",
        review_type=body.review_type,
        notes=body.notes,
    )
    db.add(assignment)

    # Transition case to expert_review if not already
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one()
    if case.status in ("open", "under_review", "intake"):
        case.status = "expert_review"

    await db.flush()

    await emit_audit_event(
        db, "expert_assigned", user.id, "case", case_id,
        {"reviewer": reviewer.username, "review_type": body.review_type}
    )

    result = await db.execute(
        select(ReviewAssignment)
        .where(ReviewAssignment.id == assignment.id)
        .options(selectinload(ReviewAssignment.reviewer), selectinload(ReviewAssignment.assigner))
    )
    assignment = result.scalar_one()
    log.info("Case %s assigned to %s by %s", case_id, reviewer.username, user.username)
    return _serialize_assignment(assignment)


@router.post("/cases/{case_id}/claim")
async def claim_assignment(case_id: UUID, db: DB, user: CurrentUser):
    """Expert: claim a pending assignment (self-service review)."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    # Find a pending assignment for this expert+case, or create a self-claim
    result = await db.execute(
        select(ReviewAssignment).where(
            ReviewAssignment.case_id == case_id,
            ReviewAssignment.assigned_to == user.id,
            ReviewAssignment.status == "pending",
        ).options(selectinload(ReviewAssignment.reviewer), selectinload(ReviewAssignment.assigner))
    )
    assignment = result.scalar_one_or_none()

    if assignment is None:
        # Self-claim: create a primary assignment
        case_result = await db.execute(
            select(Case).where(Case.id == case_id, Case.is_archived == False)
        )
        if case_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"detail": "Case not found", "code": "not_found"},
            )
        assignment = ReviewAssignment(
            case_id=case_id,
            assigned_to=user.id,
            assigned_by=user.id,
            status="claimed",
            review_type="primary",
            claimed_at=datetime.now(timezone.utc),
        )
        db.add(assignment)

        # Update case status
        case_result2 = await db.execute(select(Case).where(Case.id == case_id))
        case = case_result2.scalar_one()
        if case.status in ("open", "under_review", "intake"):
            case.status = "expert_review"

    else:
        assignment.status = "claimed"
        assignment.claimed_at = datetime.now(timezone.utc)

    await db.flush()

    await emit_audit_event(
        db, "assignment_claimed", user.id, "case", case_id,
        {"reviewer": user.username}
    )
    await award_reputation(db, user.id, "assignment_claimed", "case", case_id)

    result = await db.execute(
        select(ReviewAssignment)
        .where(ReviewAssignment.id == assignment.id)
        .options(selectinload(ReviewAssignment.reviewer), selectinload(ReviewAssignment.assigner))
    )
    return _serialize_assignment(result.scalar_one())


@router.post("/cases/{case_id}/escalate")
async def escalate_case(
    case_id: UUID,
    db: DB,
    user: CurrentUser,
    reason: str = Query("Secondary review requested"),
):
    """Expert/admin: escalate a case for secondary review."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    case = case_result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    old_status = case.status
    case.status = "escalated"

    await emit_audit_event(
        db, "case_escalated", user.id, "case", case_id,
        {"from": old_status, "reason": reason, "by": user.username}
    )

    return {"case_id": str(case_id), "status": "escalated", "reason": reason}


@router.get("/reviews/queue")
async def get_review_queue(db: DB, user: CurrentUser):
    """Expert: get cases assigned to me or available for claim."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    # Cases assigned to this user (pending/claimed/in_review)
    assigned_result = await db.execute(
        select(ReviewAssignment)
        .where(
            ReviewAssignment.assigned_to == user.id,
            ReviewAssignment.status.in_(["pending", "claimed", "in_review"]),
        )
        .options(
            selectinload(ReviewAssignment.case),
            selectinload(ReviewAssignment.reviewer),
            selectinload(ReviewAssignment.assigner),
        )
        .order_by(ReviewAssignment.created_at.desc())
    )
    assignments = assigned_result.scalars().all()

    # Cases in expert_review with no assignment to this expert (available to claim)
    from sqlalchemy import not_, exists
    claimable_result = await db.execute(
        select(Case)
        .where(
            Case.status == "expert_review",
            Case.is_archived == False,
            not_(
                exists().where(
                    ReviewAssignment.case_id == Case.id,
                    ReviewAssignment.assigned_to == user.id,
                    ReviewAssignment.status.notin_(["declined", "complete"]),
                )
            ),
        )
        .order_by(Case.created_at.asc())
        .limit(20)
    )
    claimable_cases = claimable_result.scalars().all()

    return {
        "assigned": [_serialize_assignment(a) for a in assignments],
        "claimable": [
            {
                "id": str(c.id),
                "title": c.title,
                "status": c.status,
                "setting": c.setting,
                "created_at": c.created_at.isoformat(),
            }
            for c in claimable_cases
        ],
    }


# ─── Evidence Locks ───────────────────────────────────────────────────────────

@router.post("/cases/{case_id}/lock", status_code=status.HTTP_201_CREATED)
async def lock_evidence(case_id: UUID, body: EvidenceLockCreate, db: DB, user: CurrentUser):
    """Expert/admin: lock case evidence after resolution."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    case = case_result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    if case.status not in ("resolved", "expert_review", "consensus_pending"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": f"Cannot lock a case with status '{case.status}'. Must be resolved first.",
                "code": "invalid_state",
            },
        )

    existing = await db.execute(
        select(EvidenceLock).where(EvidenceLock.case_id == case_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Case evidence is already locked", "code": "conflict"},
        )

    # Build snapshot of current state
    snapshot = await build_case_snapshot(db, case_id)

    lock = EvidenceLock(
        case_id=case_id,
        locked_by=user.id,
        lock_state=body.lock_state,
        reason=body.reason,
        snapshot=snapshot,
    )
    db.add(lock)
    case.status = "locked"

    await db.flush()

    await emit_audit_event(
        db, "case_locked", user.id, "case", case_id,
        {"lock_state": body.lock_state, "reason": body.reason}
    )

    log.info("Case %s locked by %s", case_id, user.username)

    result = await db.execute(
        select(EvidenceLock)
        .where(EvidenceLock.id == lock.id)
        .options(selectinload(EvidenceLock.locker))
    )
    lock = result.scalar_one()
    return _serialize_lock(lock, user.username)


@router.get("/cases/{case_id}/lock")
async def get_evidence_lock(case_id: UUID, db: DB):
    """Get the evidence lock for a case (if it exists)."""
    result = await db.execute(
        select(EvidenceLock)
        .where(EvidenceLock.case_id == case_id)
        .options(selectinload(EvidenceLock.locker))
    )
    lock = result.scalar_one_or_none()
    if lock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "No evidence lock on this case", "code": "not_found"},
        )
    return _serialize_lock(lock, lock.locker.username)


@router.delete("/cases/{case_id}/lock", status_code=status.HTTP_204_NO_CONTENT)
async def unlock_evidence(case_id: UUID, db: DB, user: CurrentUser):
    """Admin only: remove an evidence lock (unlock)."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required for unlock", "code": "forbidden"},
        )

    result = await db.execute(
        select(EvidenceLock).where(EvidenceLock.case_id == case_id)
    )
    lock = result.scalar_one_or_none()
    if lock is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "No evidence lock on this case", "code": "not_found"},
        )

    await db.delete(lock)

    # Revert case to resolved
    case_result = await db.execute(select(Case).where(Case.id == case_id))
    case = case_result.scalar_one_or_none()
    if case and case.status == "locked":
        case.status = "resolved"

    await emit_audit_event(
        db, "case_unlocked", user.id, "case", case_id,
        {"unlocked_by": user.username}
    )

    log.info("Case %s unlocked by admin %s", case_id, user.username)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _serialize_assignment(a: ReviewAssignment) -> AssignmentResponse:
    return AssignmentResponse(
        id=a.id,
        case_id=a.case_id,
        reviewer_username=a.reviewer.username,
        assigner_username=a.assigner.username,
        status=a.status,
        review_type=a.review_type,
        notes=a.notes,
        claimed_at=a.claimed_at,
        completed_at=a.completed_at,
        created_at=a.created_at,
    )


def _serialize_lock(lock: EvidenceLock, locked_by_username: str) -> EvidenceLockResponse:
    return EvidenceLockResponse(
        id=lock.id,
        case_id=lock.case_id,
        locked_by_username=locked_by_username,
        locked_at=lock.locked_at,
        lock_state=lock.lock_state,
        reason=lock.reason,
        snapshot=lock.snapshot or {},
        created_at=lock.created_at,
    )
