import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.case import Case
    from app.models.user import User


class ExpertResolution(UUIDMixin, FullTimestampMixin, Base):
    __tablename__ = "expert_resolutions"
    __table_args__ = (UniqueConstraint("case_id", name="uq_resolution_per_case"),)

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id"), nullable=False
    )
    expert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    verdict: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence_level: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    case: Mapped["Case"] = relationship(
        "Case", back_populates="expert_resolution", lazy="raise"
    )
    expert: Mapped["User"] = relationship(
        "User", back_populates="expert_resolutions", lazy="raise"
    )
