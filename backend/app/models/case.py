import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.case_media import CaseMedia
    from app.models.case_tag import CaseTag
    from app.models.annotation import Annotation
    from app.models.comment import Comment
    from app.models.resolution import ExpertResolution


class Case(UUIDMixin, FullTimestampMixin, Base):
    __tablename__ = "cases"

    submitter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="open")
    species_context: Mapped[str] = mapped_column(Text, nullable=False, default="dog")
    setting: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject_age_estimate: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    subject_breed_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trigger_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_summary_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    view_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    submitter: Mapped["User"] = relationship(
        "User", back_populates="submitted_cases", lazy="raise"
    )
    media: Mapped[List["CaseMedia"]] = relationship(
        "CaseMedia", back_populates="case", lazy="raise", cascade="all, delete-orphan"
    )
    case_tags: Mapped[List["CaseTag"]] = relationship(
        "CaseTag", back_populates="case", lazy="raise", cascade="all, delete-orphan"
    )
    annotations: Mapped[List["Annotation"]] = relationship(
        "Annotation", back_populates="case", lazy="raise", cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="case", lazy="raise", cascade="all, delete-orphan"
    )
    expert_resolution: Mapped[Optional["ExpertResolution"]] = relationship(
        "ExpertResolution",
        back_populates="case",
        lazy="raise",
        uselist=False,
        cascade="all, delete-orphan",
    )
