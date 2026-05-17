"""
Export job — audit record for every data export request.

Every export is logged for traceability and compliance.
Export jobs are immutable after completion — they cannot be re-run
(a new job must be created).
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import User


class ExportJob(UUIDMixin, TimestampMixin, Base):
    """
    Tracks every export request. Serves as the audit record for data access.

    status values: 'pending' | 'generating' | 'ready' | 'failed'
    format values: 'json' | 'csv' | 'ndjson'
    export_type values: 'cases' | 'annotations' | 'audit' | 'experts' | 'consensus' | 'full_dataset'
    """

    __tablename__ = "export_jobs"

    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    export_type: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")

    # Filter parameters used for this export
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Result metadata (set on completion)
    record_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # For future async file storage
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    requester: Mapped["User"] = relationship("User", lazy="raise")
