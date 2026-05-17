import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.tag import Tag
    from app.models.user import User


class CaseTag(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "case_tags"
    __table_args__ = (UniqueConstraint("case_id", "tag_id", "applied_by", name="uq_case_tag_user"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False
    )
    applied_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    confidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case: Mapped["Case"] = relationship("Case", back_populates="case_tags", lazy="raise")
    tag: Mapped["Tag"] = relationship("Tag", lazy="raise")
    applied_by_user: Mapped["User"] = relationship("User", lazy="raise")
