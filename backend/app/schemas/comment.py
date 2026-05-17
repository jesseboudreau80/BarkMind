from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    body: str = Field(min_length=1)
    parent_id: UUID | None = None


class CommentResponse(BaseModel):
    id: UUID
    case_id: UUID
    author_username: str
    body: str
    parent_id: UUID | None
    is_archived: bool
    replies: list["CommentResponse"] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


CommentResponse.model_rebuild()
