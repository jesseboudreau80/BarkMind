"""
Event publisher — structured event bus abstraction over the audit_events table.

Design principles:
- Append-only: events are never modified after creation
- Typed: each event type has a Pydantic schema
- Replayable: query by since= timestamp for event replay
- Filterable: by type, actor, target, time range
- Abstracted: router code doesn't know the storage backend

Current storage: PostgreSQL audit_events table.
Future migration path: swap _persist_event() to emit to Kafka/NATS/SQS
without changing any caller code.

Event types are documented in docs/GOVERNANCE_MODEL.md.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger("barkmind.events")


# ─── Typed Event Schemas ──────────────────────────────────────────────────────

class BaseEvent(BaseModel):
    """Base schema for all BarkMind events."""
    event_type: str
    actor_id: UUID | None = None
    target_type: str
    target_id: UUID | None = None
    metadata: dict[str, Any] = {}


class CaseLifecycleEvent(BaseEvent):
    target_type: str = "case"


class AnnotationEvent(BaseEvent):
    target_type: str = "annotation"


class ConsensusEvent(BaseEvent):
    target_type: str = "case"


class ExpertEvent(BaseEvent):
    target_type: str = "user"


class EvidenceEvent(BaseEvent):
    target_type: str = "case"


class GovernanceEvent(BaseEvent):
    pass


# ─── Event Constructors ───────────────────────────────────────────────────────

def case_created(actor_id: UUID, case_id: UUID, title: str, setting: str | None) -> CaseLifecycleEvent:
    return CaseLifecycleEvent(
        event_type="case_created",
        actor_id=actor_id,
        target_id=case_id,
        metadata={"title": title, "setting": setting},
    )


def case_resolved(actor_id: UUID, case_id: UUID, verdict: str) -> CaseLifecycleEvent:
    return CaseLifecycleEvent(
        event_type="case_resolved",
        actor_id=actor_id,
        target_id=case_id,
        metadata={"verdict": verdict},
    )


def annotation_created(actor_id: UUID, annotation_id: UUID, case_id: UUID, ann_type: str) -> AnnotationEvent:
    return AnnotationEvent(
        event_type="annotation_created",
        actor_id=actor_id,
        target_id=annotation_id,
        metadata={"case_id": str(case_id), "annotation_type": ann_type},
    )


def consensus_reached(actor_id: UUID, case_id: UUID, verdict: str, confidence: str | None) -> ConsensusEvent:
    return ConsensusEvent(
        event_type="consensus_reached",
        actor_id=actor_id,
        target_id=case_id,
        metadata={"verdict": verdict, "confidence": confidence},
    )


def evidence_locked(actor_id: UUID, case_id: UUID, lock_state: str) -> EvidenceEvent:
    return EvidenceEvent(
        event_type="evidence_locked",
        actor_id=actor_id,
        target_id=case_id,
        metadata={"lock_state": lock_state},
    )


def export_requested(actor_id: UUID, export_id: UUID, export_type: str, fmt: str) -> GovernanceEvent:
    return GovernanceEvent(
        event_type="export_requested",
        actor_id=actor_id,
        target_type="export",
        target_id=export_id,
        metadata={"export_type": export_type, "format": fmt},
    )


def dataset_snapshot_created(actor_id: UUID, snapshot_id: UUID, name: str, case_count: int) -> GovernanceEvent:
    return GovernanceEvent(
        event_type="dataset_snapshot_created",
        actor_id=actor_id,
        target_type="snapshot",
        target_id=snapshot_id,
        metadata={"name": name, "case_count": case_count},
    )


# ─── Publisher ────────────────────────────────────────────────────────────────

async def publish(db: AsyncSession, event: BaseEvent) -> None:
    """
    Publish an event to the event store.

    Currently persists to audit_events. Future: add message broker emission here.
    """
    from app.services.governance import emit_audit_event

    await emit_audit_event(
        db=db,
        event_type=event.event_type,
        actor_id=event.actor_id,
        target_type=event.target_type,
        target_id=event.target_id,
        metadata=event.metadata,
    )
    log.debug("Published event: %s → %s:%s", event.event_type, event.target_type, event.target_id)


# ─── Event Stream Query ───────────────────────────────────────────────────────

async def get_event_stream(
    db: AsyncSession,
    since: datetime | None = None,
    event_type: str | None = None,
    target_type: str | None = None,
    actor_id: UUID | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict]:
    """
    Query the event stream with filtering and pagination.

    This is the event replay mechanism — callers can reconstruct state
    by replaying events from a given timestamp forward.
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.audit_event import AuditEvent

    stmt = (
        select(AuditEvent)
        .options(selectinload(AuditEvent.actor))
        .order_by(AuditEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
    )

    if since:
        stmt = stmt.where(AuditEvent.created_at >= since)
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    if target_type:
        stmt = stmt.where(AuditEvent.target_type == target_type)
    if actor_id:
        stmt = stmt.where(AuditEvent.actor_id == actor_id)

    result = await db.execute(stmt)
    events = result.scalars().all()

    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "actor": e.actor.username if e.actor else None,
            "target_type": e.target_type,
            "target_id": str(e.target_id) if e.target_id else None,
            "metadata": e.event_metadata,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]
