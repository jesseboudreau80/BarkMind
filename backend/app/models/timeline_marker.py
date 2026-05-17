"""
Timeline markers for behavioral events within a video case.

Markers pin a named behavioral event to a specific timestamp, creating
a structured behavioral timeline that serves as a foundation for:
- Expert annotation workflows
- Future AI frame selection
- Dataset labeling for temporal behavior models
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.user import User
    from app.models.case_media import CaseMedia


class TimelineMarker(UUIDMixin, FullTimestampMixin, Base):
    __tablename__ = "timeline_markers"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    # Optional: associate with a specific media file (needed for multi-media cases)
    media_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_media.id"), nullable=True
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Position in the video
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)

    # What this moment is
    label: Mapped[str] = mapped_column(Text, nullable=False)

    # Controlled vocabulary for marker type — extensible via taxonomy in future
    # Values: event, escalation, de_escalation, handler_intervention,
    #         trigger, resolution, calming_signal, threshold_break
    marker_type: Mapped[str] = mapped_column(Text, nullable=False, default="event")

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_expert: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    case: Mapped["Case"] = relationship("Case", lazy="raise")
    media: Mapped[Optional["CaseMedia"]] = relationship("CaseMedia", lazy="raise")
    author: Mapped["User"] = relationship("User", lazy="raise")
