from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

VERDICTS = {"safe", "concern", "escalation_risk", "requires_intervention"}
CONSENSUS_STATUSES = {"open", "reached", "disputed", "escalated"}


class ConsensusInitiate(BaseModel):
    notes: str | None = None


class ExpertOpinionCreate(BaseModel):
    verdict: str
    confidence_level: str | None = None
    summary: str | None = None


class ExpertOpinionResponse(BaseModel):
    id: UUID
    expert_username: str
    verdict: str
    confidence_level: str | None
    summary: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConsensusResponse(BaseModel):
    id: UUID
    case_id: UUID
    status: str
    initiated_by_username: str
    verdict_tally: dict
    consensus_verdict: str | None
    consensus_confidence: str | None
    notes: str | None
    opinion_count: int
    opinions: list[ExpertOpinionResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
