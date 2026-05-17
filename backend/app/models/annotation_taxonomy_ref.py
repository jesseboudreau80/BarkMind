"""
Join table linking annotations to taxonomy terms.

One annotation can reference multiple taxonomy terms.
One taxonomy term can appear in multiple annotations.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.annotation import Annotation
    from app.models.taxonomy import TaxonomyTerm


class AnnotationTaxonomyRef(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "annotation_taxonomy_refs"
    __table_args__ = (
        UniqueConstraint(
            "annotation_id", "taxonomy_term_id", name="uq_annotation_taxonomy_ref"
        ),
    )

    annotation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("annotations.id", ondelete="CASCADE"),
        nullable=False,
    )
    taxonomy_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("taxonomy_terms.id"),
        nullable=False,
    )

    annotation: Mapped["Annotation"] = relationship(
        "Annotation", back_populates="taxonomy_refs", lazy="raise"
    )
    term: Mapped["TaxonomyTerm"] = relationship(
        "TaxonomyTerm", back_populates="annotation_refs", lazy="raise"
    )
