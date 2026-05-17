"""
Dataset snapshot — point-in-time metadata capture of the BarkMind dataset.

A snapshot records the state of the behavioral intelligence dataset at a specific moment.
It does NOT contain the full data (that's what exports are for) — it is a versioned
metadata record that enables dataset version tracking, citation, and provenance.

snapshot_metadata JSONB contains aggregate statistics:
{
  "case_count": N,
  "resolved_case_count": N,
  "locked_case_count": N,
  "annotation_count": N,
  "expert_annotation_count": N,
  "taxonomy_term_count": N,
  "taxonomy_ref_count": N,
  "consensus_count": N,
  "expert_count": N,
  "timeline_marker_count": N,
  "media_count": N,
  "status_distribution": {...},
  "setting_distribution": {...},
  "verdict_distribution": {...},
  "top_taxonomy_terms": [...],
}
"""
import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class DatasetSnapshot(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "dataset_snapshots"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # Version identifier (semver or date-based)
    version_tag: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Aggregate counts for quick reference
    case_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    annotation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expert_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Full statistics snapshot
    snapshot_metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    creator: Mapped["User"] = relationship("User", lazy="raise")
