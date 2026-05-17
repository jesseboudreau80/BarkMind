from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TaxonomyTermResponse(BaseModel):
    id: UUID
    slug: str
    label: str
    category: str
    parent_id: UUID | None
    description: str | None
    sort_order: int
    is_active: bool
    term_metadata: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class TaxonomyGroupedResponse(BaseModel):
    """All active taxonomy terms organized by category."""
    categories: dict[str, list[TaxonomyTermResponse]]
    total: int


class TaxonomyTermCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9_]+$", min_length=2, max_length=80)
    label: str = Field(min_length=2, max_length=200)
    category: str = Field(min_length=2, max_length=80)
    parent_id: UUID | None = None
    description: str | None = None
    sort_order: int = 0
    term_metadata: dict = {}


class TaxonomyTermPatch(BaseModel):
    label: str | None = None
    description: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
    term_metadata: dict | None = None


class AnnotationTaxonomyRefResponse(BaseModel):
    id: UUID
    taxonomy_term_id: UUID
    term: TaxonomyTermResponse
    created_at: datetime

    model_config = {"from_attributes": True}
