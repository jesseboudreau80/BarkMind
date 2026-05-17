from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

ASSIGNMENT_STATUSES = {
    "pending", "claimed", "in_review", "complete", "transferred", "declined"
}
REVIEW_TYPES = {"primary", "secondary", "escalation"}


class AssignmentCreate(BaseModel):
    assigned_to_username: str
    review_type: str = "primary"
    notes: str | None = None


class AssignmentResponse(BaseModel):
    id: UUID
    case_id: UUID
    reviewer_username: str
    assigner_username: str
    status: str
    review_type: str
    notes: str | None
    claimed_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvidenceLockCreate(BaseModel):
    lock_state: str = "full"
    reason: str | None = None


class EvidenceLockResponse(BaseModel):
    id: UUID
    case_id: UUID
    locked_by_username: str
    locked_at: datetime
    lock_state: str
    reason: str | None
    snapshot: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseStatusUpdate(BaseModel):
    status: str
    reason: str | None = None
