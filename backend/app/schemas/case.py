from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.user import UserBrief
from app.schemas.tag import CaseTagResponse
from app.schemas.media import MediaResponse


class AnnotationResponse(BaseModel):
    id: UUID
    annotation_type: str
    body: str
    extra_data: dict
    timestamp_start: float | None
    timestamp_end: float | None
    is_expert: bool
    author_username: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResolutionResponse(BaseModel):
    id: UUID
    verdict: str
    summary: str
    recommendations: str | None
    confidence_level: str | None
    expert_username: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseCreate(BaseModel):
    title: str = Field(min_length=5, max_length=300)
    description: str | None = None
    setting: str | None = None
    subject_age_estimate: str | None = None
    subject_breed_note: str | None = None
    trigger_context: str | None = None


class CasePatch(BaseModel):
    title: str | None = None
    description: str | None = None
    setting: str | None = None
    subject_age_estimate: str | None = None
    subject_breed_note: str | None = None
    trigger_context: str | None = None


class CaseListItem(BaseModel):
    id: UUID
    title: str
    status: str
    setting: str | None
    subject_age_estimate: str | None
    submitter: UserBrief
    view_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseListResponse(BaseModel):
    items: list[CaseListItem]
    next_cursor: str | None
    has_more: bool


class CaseDetail(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: str
    setting: str | None
    subject_age_estimate: str | None
    subject_breed_note: str | None
    trigger_context: str | None
    species_context: str
    submitter: UserBrief
    tags: list[CaseTagResponse]
    annotations: list[AnnotationResponse]
    media: list[MediaResponse]
    comments_count: int
    expert_resolution: ResolutionResponse | None
    ai_summary: str | None
    view_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CaseCreatedResponse(BaseModel):
    id: UUID
    status: str
    created_at: datetime
