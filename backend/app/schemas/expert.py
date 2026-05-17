from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CertificationEntry(BaseModel):
    name: str
    issuer: str | None = None
    year: int | None = None
    expiry_year: int | None = None


class ExpertProfileCreate(BaseModel):
    display_title: str | None = None
    organization: str | None = None
    bio_professional: str | None = None
    years_experience: int | None = Field(None, ge=0, le=60)
    certifications: list[CertificationEntry] = []
    specializations: list[str] = []


class ExpertProfilePatch(BaseModel):
    display_title: str | None = None
    organization: str | None = None
    bio_professional: str | None = None
    years_experience: int | None = None
    certifications: list[CertificationEntry] | None = None
    specializations: list[str] | None = None


class ExpertProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    username: str
    display_name: str | None
    display_title: str | None
    organization: str | None
    bio_professional: str | None
    years_experience: int | None
    certifications: list[CertificationEntry]
    specializations: list[str]
    verification_status: str
    verified_at: datetime | None
    review_count: int
    annotation_count: int
    consensus_agreement_count: int
    reputation_score: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ExpertVerifyRequest(BaseModel):
    verification_status: str = Field(pattern="^(verified|unverified|pending)$")


class ExpertStatsResponse(BaseModel):
    username: str
    reputation_score: int
    review_count: int
    annotation_count: int
    consensus_agreement_count: int
    verification_status: str
    specializations: list[str]
