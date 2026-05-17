"""
Consensus review system — multi-expert opinion aggregation.

ConsensusRecord: one per case, tracks the overall consensus process.
ExpertOpinion: one per expert per consensus, their individual verdict.

Status flow:
  open → reached (majority alignment)
  open → disputed (no majority)
  open → escalated (sent to senior review)

verdict_tally JSONB: {"safe": 2, "concern": 1, "escalation_risk": 0, "requires_intervention": 0}
participating_experts JSONB: [user_id_str, ...]
"""
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.user import User


class ConsensusRecord(UUIDMixin, FullTimestampMixin, Base):
    __tablename__ = "consensus_records"
    __table_args__ = (UniqueConstraint("case_id", name="uq_consensus_per_case"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    initiated_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(Text, nullable=False, default="open")

    # Denormalized vote tally — updated on each opinion submission
    verdict_tally: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Computed when consensus is reached
    consensus_verdict: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consensus_confidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case: Mapped["Case"] = relationship("Case", lazy="raise")
    initiator: Mapped["User"] = relationship(
        "User", foreign_keys=[initiated_by], lazy="raise"
    )
    opinions: Mapped[List["ExpertOpinion"]] = relationship(
        "ExpertOpinion",
        back_populates="consensus",
        lazy="raise",
        cascade="all, delete-orphan",
    )


class ExpertOpinion(UUIDMixin, FullTimestampMixin, Base):
    """An individual expert's opinion within a consensus review."""

    __tablename__ = "expert_opinions"
    __table_args__ = (
        UniqueConstraint("consensus_id", "expert_id", name="uq_opinion_per_expert"),
    )

    consensus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consensus_records.id"), nullable=False
    )
    expert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    verdict: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    consensus: Mapped["ConsensusRecord"] = relationship(
        "ConsensusRecord", back_populates="opinions", lazy="raise"
    )
    expert: Mapped["User"] = relationship("User", lazy="raise")
