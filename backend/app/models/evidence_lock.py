"""
Evidence lock — immutable snapshot of case state after resolution.

When a case is locked:
1. A snapshot of the case state is stored in JSONB
2. New annotations are blocked
3. Existing annotations cannot be edited
4. Media cannot be deleted

lock_state values:
  'media'      — media files locked, annotations still editable
  'full'       — both media and annotations locked (default for resolved cases)

The snapshot field captures the complete reviewable state at lock time,
serving as the permanent record for the behavioral intelligence dataset.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.user import User


class EvidenceLock(UUIDMixin, TimestampMixin, Base):
    """
    Created once per case when locked. Never updated — the record is immutable.
    """

    __tablename__ = "evidence_locks"
    __table_args__ = (UniqueConstraint("case_id", name="uq_lock_per_case"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    locked_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    locked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=__import__("sqlalchemy").func.now(),
    )
    lock_state: Mapped[str] = mapped_column(Text, nullable=False, default="full")
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Immutable snapshot of case state at lock time
    # Contains: verdict, annotation count, tag count, media count, submitter, resolution
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    case: Mapped["Case"] = relationship("Case", lazy="raise")
    locker: Mapped["User"] = relationship("User", lazy="raise")
