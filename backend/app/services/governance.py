"""
Governance service — audit events and reputation management.

This service is called from routers after significant actions.
It writes immutable audit records and updates reputation scores atomically.

No AI. No algorithmic scoring. Pure event-driven human signal accumulation.
"""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_event import AuditEvent
from app.models.reputation_event import ReputationEvent
from app.models.user import User
from sqlalchemy import select

log = logging.getLogger("barkmind.governance")

# Reputation deltas by event type
REPUTATION_DELTAS: dict[str, int] = {
    "resolution_submitted": 5,
    "resolution_accepted": 3,
    "consensus_aligned": 2,
    "consensus_dissented": -1,
    "secondary_review_requested": -1,
    "annotation_on_resolved_case": 1,
    "assignment_claimed": 1,
    "expert_verified": 10,
}


async def emit_audit_event(
    db: AsyncSession,
    event_type: str,
    actor_id: UUID | None,
    target_type: str,
    target_id: UUID | None = None,
    metadata: dict | None = None,
) -> AuditEvent:
    """
    Write an immutable audit event record.

    Call this after any significant governance action.
    Audit events are never updated or deleted.
    """
    event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        target_type=target_type,
        target_id=target_id,
        event_metadata=metadata or {},
    )
    db.add(event)
    log.info(
        "AUDIT: %s by actor=%s on %s:%s",
        event_type,
        actor_id,
        target_type,
        target_id,
    )
    return event


async def award_reputation(
    db: AsyncSession,
    user_id: UUID,
    event_type: str,
    reference_type: str | None = None,
    reference_id: UUID | None = None,
    override_delta: int | None = None,
) -> int:
    """
    Award (or deduct) reputation for a user.

    Returns the delta applied.
    Does NOT flush or commit — caller is responsible.
    """
    delta = override_delta if override_delta is not None else REPUTATION_DELTAS.get(event_type, 0)
    if delta == 0:
        return 0

    # Reputation event record
    rep_event = ReputationEvent(
        user_id=user_id,
        event_type=event_type,
        delta=delta,
        reference_type=reference_type,
        reference_id=reference_id,
    )
    db.add(rep_event)

    # Update denormalized reputation_score on User
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.reputation_score = max(0, user.reputation_score + delta)
        log.info(
            "REPUTATION: user=%s event=%s delta=%+d new_score=%d",
            user_id,
            event_type,
            delta,
            user.reputation_score,
        )

    return delta
