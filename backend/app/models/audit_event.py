"""
Immutable audit event log for governance visibility.

Every significant governance action creates an audit event.
Audit events are NEVER updated or deleted.

event_type values (not exhaustive — extensible via metadata):
  case_status_changed       — case.status was updated
  resolution_submitted      — expert_resolution created
  resolution_updated        — expert_resolution patched
  case_locked               — evidence_lock created
  case_unlocked             — evidence_lock removed (admin)
  expert_assigned           — review_assignment created
  assignment_claimed        — review_assignment status → claimed
  assignment_transferred    — review_assignment transferred
  case_escalated            — review type escalated
  consensus_initiated       — consensus_record created
  consensus_opinion_added   — expert_opinion submitted
  consensus_reached         — consensus_record status → reached
  expert_verified           — expert_profile verification_status → verified
  annotation_locked         — annotation made immutable by lock
  user_role_changed         — user.role updated by admin

target_type values: 'case' | 'user' | 'annotation' | 'resolution' | 'assignment' | 'consensus'
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditEvent(UUIDMixin, TimestampMixin, Base):
    """
    Write-once audit record. No updated_at — immutable by design.
    """

    __tablename__ = "audit_events"

    event_type: Mapped[str] = mapped_column(Text, nullable=False)

    # Who triggered this event
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # What was affected
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Event-specific data (old_value, new_value, reason, etc.)
    event_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    actor: Mapped[Optional["User"]] = relationship("User", lazy="raise")
