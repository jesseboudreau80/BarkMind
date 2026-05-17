"""
Expert profile — extended credentials and verification for expert-role users.

Separate from the User model so non-experts don't carry the overhead.
One-to-one with users.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class ExpertProfile(UUIDMixin, FullTimestampMixin, Base):
    """
    Extended professional profile for verified behavioral experts.

    verification_status values:
      'unverified'  — profile created, not yet reviewed
      'pending'     — verification request submitted
      'verified'    — admin has confirmed credentials

    certifications JSONB: [{name, issuer, year, expiry_year}]
    specializations JSONB: ["daycare", "shelter", "reactivity", ...]
    """

    __tablename__ = "expert_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_expert_profile_user"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Professional identity
    display_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    organization: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bio_professional: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    years_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Structured credentials (extensible JSONB)
    certifications: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    specializations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Verification
    verification_status: Mapped[str] = mapped_column(
        Text, nullable=False, default="unverified"
    )
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        __import__("sqlalchemy").DateTime(timezone=True), nullable=True
    )

    # Denormalized counters (updated on write, avoid expensive COUNT queries)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    annotation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    consensus_agreement_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], lazy="raise"
    )
    verifier: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[verified_by], lazy="raise"
    )
