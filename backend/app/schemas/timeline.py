from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

MARKER_TYPES = {
    "event",
    "escalation",
    "de_escalation",
    "handler_intervention",
    "trigger",
    "resolution",
    "calming_signal",
    "threshold_break",
    "play_initiation",
    "resource_guard",
}


class TimelineMarkerCreate(BaseModel):
    timestamp_seconds: float = Field(ge=0)
    label: str = Field(min_length=1, max_length=200)
    marker_type: str = "event"
    media_id: UUID | None = None
    notes: str | None = None


class TimelineMarkerResponse(BaseModel):
    id: UUID
    case_id: UUID
    media_id: UUID | None
    author_username: str
    timestamp_seconds: float
    label: str
    marker_type: str
    notes: str | None
    is_expert: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TimelineMarkerPatch(BaseModel):
    label: str | None = None
    marker_type: str | None = None
    notes: str | None = None
    timestamp_seconds: float | None = None
