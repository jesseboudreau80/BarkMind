"""
Review assignments — tracks which expert is reviewing which case.

Assignment lifecycle:
  pending → claimed → in_review → complete
  pending → declined
  in_review → transferred → (new assignment created)
  in_review → escalated (escalation_review created)

review_type values:
  'primary'    — initial expert review
  'secondary'  — second opinion requested
  'escalation' — escalated from primary reviewer
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.user import User


class ReviewAssignment(UUIDMixin, FullTimestampMixin, Base):
    __tablename__ = "review_assignments"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    assigned_to: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    assigned_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    review_type: Mapped[str] = mapped_column(Text, nullable=False, default="primary")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Lifecycle timestamps
    claimed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Transfer chain
    transferred_from: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("review_assignments.id"), nullable=True
    )

    case: Mapped["Case"] = relationship("Case", lazy="raise")
    reviewer: Mapped["User"] = relationship(
        "User", foreign_keys=[assigned_to], lazy="raise"
    )
    assigner: Mapped["User"] = relationship(
        "User", foreign_keys=[assigned_by], lazy="raise"
    )
    parent_assignment: Mapped[Optional["ReviewAssignment"]] = relationship(
        "ReviewAssignment", remote_side="ReviewAssignment.id", lazy="raise"
    )
