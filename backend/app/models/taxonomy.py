"""
Behavioral taxonomy for structured canine behavioral annotation.

Design principles:
- Flat by default, hierarchical via parent_id (future)
- Extensible via metadata JSONB
- Never hardcoded — categories and terms are data, not code
- Versioned via created_at/updated_at for future export audit
"""
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, FullTimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.annotation_taxonomy_ref import AnnotationTaxonomyRef


class TaxonomyTerm(UUIDMixin, FullTimestampMixin, Base):
    """
    A single term in the behavioral taxonomy.

    Terms are organized by category (e.g., "tail_position", "stress_indicators").
    parent_id enables sub-categorization within a category.
    metadata JSONB stores extensible properties (severity_hint, body_region, etc.).
    """

    __tablename__ = "taxonomy_terms"

    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional hierarchy — parent_id enables nested taxonomy (e.g., sub-categories)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("taxonomy_terms.id"),
        nullable=True,
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Extensible metadata: {severity_hint: 0-4, body_region: str, signal_type: str, ...}
    term_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Self-referential hierarchy
    parent: Mapped[Optional["TaxonomyTerm"]] = relationship(
        "TaxonomyTerm",
        remote_side="TaxonomyTerm.id",
        back_populates="children",
        lazy="raise",
    )
    children: Mapped[List["TaxonomyTerm"]] = relationship(
        "TaxonomyTerm",
        back_populates="parent",
        lazy="raise",
    )

    # Annotation references
    annotation_refs: Mapped[List["AnnotationTaxonomyRef"]] = relationship(
        "AnnotationTaxonomyRef",
        back_populates="term",
        lazy="raise",
    )
