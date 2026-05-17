from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TagResponse(BaseModel):
    id: UUID
    slug: str
    label: str
    category: str
    description: str | None
    severity_hint: int

    model_config = {"from_attributes": True}


class TagsGroupedResponse(BaseModel):
    categories: dict[str, list[TagResponse]]


class CaseTagResponse(BaseModel):
    id: UUID
    tag: TagResponse
    confidence: str | None
    timestamp_note: str | None
    applied_by_username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ApplyTagRequest(BaseModel):
    tag_slug: str
    confidence: str | None = None
    timestamp_note: str | None = None
