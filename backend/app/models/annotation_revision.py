"""
Immutable audit trail for annotation edits.

Every edit to an annotation creates a revision capturing the previous state.
Revisions are write-once and never updated — they are the audit record.
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.annotation import Annotation
    from app.models.user import User


class AnnotationRevision(UUIDMixin, TimestampMixin, Base):
    """
    Captures the state of an annotation BEFORE an edit was applied.

    created_at = the moment the revision (i.e., the edit) was saved.
    """

    __tablename__ = "annotation_revisions"

    annotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("annotations.id"),
        nullable=False,
    )
    revised_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    # Snapshot of the annotation BEFORE the edit
    previous_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_annotation_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_confidence_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Why was the edit made? (optional, encourages documentation)
    change_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    annotation: Mapped["Annotation"] = relationship(
        "Annotation", back_populates="revisions", lazy="raise"
    )
    editor: Mapped["User"] = relationship("User", lazy="raise")
