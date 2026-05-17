from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserPublic(BaseModel):
    id: UUID
    username: str
    display_name: str | None
    bio: str | None
    reputation_score: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserMe(BaseModel):
    id: UUID
    email: str
    username: str
    display_name: str | None
    bio: str | None
    role: str
    reputation_score: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UserBrief(BaseModel):
    username: str
    reputation_score: int

    model_config = {"from_attributes": True}


class UserUpdateRequest(BaseModel):
    display_name: str | None = None
    bio: str | None = None
