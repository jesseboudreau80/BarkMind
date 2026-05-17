"""
Discrete reputation change events for expert users.

Reputation is accumulated by event, not algorithmically scored.
Each event records why reputation changed and by how much.

event_type values:
  resolution_submitted     — expert submitted a resolution (+5)
  resolution_accepted      — resolution accepted without dispute (+3)
  consensus_aligned        — expert opinion matched final consensus (+2)
  consensus_dissented      — expert opinion diverged from consensus (-1)
  secondary_review_req     — someone requested a second opinion on their review (-1)
  annotation_endorsed      — expert annotated a case that later got resolved (+1)
  case_assigned            — expert accepted an assigned case (+1)

This is not AI scoring. It is structured human-signal accumulation.
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class ReputationEvent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "reputation_events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)

    # What triggered this reputation change
    reference_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", lazy="raise")
