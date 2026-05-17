"""
Organization model — multi-tenant foundation for Phase 6+.

Organizations allow scoped datasets, scoped experts, and scoped governance visibility.
This is the architectural foundation; full RBAC enforcement is post-MVP.

Design: organizations are optional. Most users have organization_id=NULL.
When an organization is assigned, export/dataset queries respect organizational scoping.
"""
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class Organization(UUIDMixin, FullTimestampMixin, Base):
    __tablename__ = "organizations"
    __table_args__ = (UniqueConstraint("slug", name="uq_org_slug"),)

    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Future: contact_email, billing_tier, feature_flags JSONB
    members: Mapped[List["User"]] = relationship(
        "User", back_populates="organization", lazy="raise"
    )
