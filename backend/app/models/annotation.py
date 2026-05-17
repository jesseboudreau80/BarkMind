import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.user import User
    from app.models.case_media import CaseMedia
    from app.models.annotation_taxonomy_ref import AnnotationTaxonomyRef
    from app.models.annotation_revision import AnnotationRevision


class Annotation(UUIDMixin, FullTimestampMixin, Base):
    __tablename__ = "annotations"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    annotation_type: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    media_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("case_media.id"), nullable=True
    )
    timestamp_start: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timestamp_end: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_expert: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Phase 4: explicit confidence level (human confidence, not AI)
    # Values: "high", "medium", "low" — NULL means unset
    confidence_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="annotations", lazy="raise")
    author: Mapped["User"] = relationship("User", back_populates="annotations", lazy="raise")
    media: Mapped[Optional["CaseMedia"]] = relationship("CaseMedia", lazy="raise")

    # Phase 4: behavioral taxonomy references
    taxonomy_refs: Mapped[List["AnnotationTaxonomyRef"]] = relationship(
        "AnnotationTaxonomyRef",
        back_populates="annotation",
        lazy="raise",
        cascade="all, delete-orphan",
    )

    # Phase 4: edit revision history (write-once audit trail)
    revisions: Mapped[List["AnnotationRevision"]] = relationship(
        "AnnotationRevision",
        back_populates="annotation",
        lazy="raise",
        order_by="AnnotationRevision.created_at.desc()",
    )
