"""
Enhanced annotation schemas for Phase 4.

These extend the Phase 1 annotation schemas with:
- Confidence levels (human-assigned)
- Behavioral taxonomy term references
- Revision history snapshots
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.taxonomy import TaxonomyTermResponse

CONFIDENCE_LEVELS = {"high", "medium", "low"}
ANNOTATION_TYPES = {"observation", "interpretation", "concern", "recommendation"}


class AnnotationTaxonomyRefOut(BaseModel):
    id: UUID
    taxonomy_term_id: UUID
    term: TaxonomyTermResponse
    created_at: datetime

    model_config = {"from_attributes": True}


class AnnotationRevisionOut(BaseModel):
    id: UUID
    revised_by_username: str
    previous_body: str | None
    previous_annotation_type: str | None
    previous_confidence_level: str | None
    previous_extra_data: dict | None
    change_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EnhancedAnnotationResponse(BaseModel):
    id: UUID
    annotation_type: str
    body: str
    extra_data: dict
    timestamp_start: float | None
    timestamp_end: float | None
    is_expert: bool
    confidence_level: str | None
    author_username: str
    taxonomy_refs: list[AnnotationTaxonomyRefOut] = []
    revision_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EnhancedAnnotationCreate(BaseModel):
    annotation_type: str
    body: str = Field(min_length=1)
    media_id: UUID | None = None
    timestamp_start: float | None = None
    timestamp_end: float | None = None
    extra_data: dict = {}
    confidence_level: str | None = None
    taxonomy_term_slugs: list[str] = Field(default_factory=list, max_length=10)


class EnhancedAnnotationPatch(BaseModel):
    body: str | None = None
    annotation_type: str | None = None
    confidence_level: str | None = None
    extra_data: dict | None = None
    change_reason: str | None = None
