import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.annotation import Annotation
    from app.models.comment import Comment
    from app.models.resolution import ExpertResolution
    from app.models.organization import Organization


class User(UUIDMixin, FullTimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False, default="user")
    display_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reputation_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Phase 6: multi-tenant foundation
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=True,
    )

    submitted_cases: Mapped[List["Case"]] = relationship(
        "Case", back_populates="submitter", lazy="raise"
    )
    annotations: Mapped[List["Annotation"]] = relationship(
        "Annotation", back_populates="author", lazy="raise"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="author", lazy="raise"
    )
    expert_resolutions: Mapped[List["ExpertResolution"]] = relationship(
        "ExpertResolution", back_populates="expert", lazy="raise"
    )
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization", back_populates="members", lazy="raise"
    )
