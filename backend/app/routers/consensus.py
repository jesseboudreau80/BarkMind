"""
Consensus review routes.

Multi-expert opinion aggregation for disputed or complex cases.
Consensus is never algorithmic — it is structured human opinion collection.

A consensus is reached when a clear majority verdict emerges.
A consensus is disputed when no majority exists.
Both states are explicit and require human action to resolve.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.case import Case
from app.models.consensus import ConsensusRecord, ExpertOpinion
from app.schemas.consensus import (
    VERDICTS,
    ConsensusInitiate,
    ConsensusResponse,
    ExpertOpinionCreate,
    ExpertOpinionResponse,
)
from app.services.governance import award_reputation, emit_audit_event

log = logging.getLogger("barkmind.consensus")
router = APIRouter(prefix="/cases", tags=["consensus"])

_VERDICT_INIT: dict = {
    "safe": 0,
    "concern": 0,
    "escalation_risk": 0,
    "requires_intervention": 0,
}


def _derive_consensus(tally: dict) -> tuple[str | None, str | None]:
    """
    Derive consensus verdict from tally.

    Returns (verdict, confidence) or (None, None) if no majority.
    Not AI — pure vote counting.
    """
    total = sum(tally.values())
    if total == 0:
        return None, None

    top_verdict = max(tally, key=lambda k: tally[k])
    top_count = tally[top_verdict]

    pct = top_count / total
    if pct >= 0.75:
        return top_verdict, "high"
    elif pct >= 0.60:
        return top_verdict, "medium"
    elif pct >= 0.50:
        return top_verdict, "low"

    return None, None  # No majority → disputed


def _serialize_consensus(record: ConsensusRecord) -> ConsensusResponse:
    opinions = [
        ExpertOpinionResponse(
            id=op.id,
            expert_username=op.expert.username,
            verdict=op.verdict,
            confidence_level=op.confidence_level,
            summary=op.summary,
            created_at=op.created_at,
        )
        for op in (record.opinions or [])
    ]
    return ConsensusResponse(
        id=record.id,
        case_id=record.case_id,
        status=record.status,
        initiated_by_username=record.initiator.username,
        verdict_tally=record.verdict_tally or dict(_VERDICT_INIT),
        consensus_verdict=record.consensus_verdict,
        consensus_confidence=record.consensus_confidence,
        notes=record.notes,
        opinion_count=len(opinions),
        opinions=opinions,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("/{case_id}/consensus")
async def get_consensus(case_id: UUID, db: DB):
    """Get the consensus record for a case."""
    result = await db.execute(
        select(ConsensusRecord)
        .where(ConsensusRecord.case_id == case_id)
        .options(
            selectinload(ConsensusRecord.initiator),
            selectinload(ConsensusRecord.opinions).selectinload(ExpertOpinion.expert),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "No consensus review for this case", "code": "not_found"},
        )
    return _serialize_consensus(record)


@router.post("/{case_id}/consensus", status_code=status.HTTP_201_CREATED)
async def initiate_consensus(
    case_id: UUID,
    body: ConsensusInitiate,
    db: DB,
    user: CurrentUser,
):
    """Expert/admin: initiate a consensus review for a case."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    case = case_result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    existing = await db.execute(
        select(ConsensusRecord).where(ConsensusRecord.case_id == case_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Consensus review already exists", "code": "conflict"},
        )

    record = ConsensusRecord(
        case_id=case_id,
        initiated_by=user.id,
        status="open",
        verdict_tally=dict(_VERDICT_INIT),
        notes=body.notes,
    )
    db.add(record)

    # Transition case to consensus_pending
    case.status = "consensus_pending"

    await db.flush()

    await emit_audit_event(
        db, "consensus_initiated", user.id, "case", case_id,
        {"initiated_by": user.username}
    )

    result = await db.execute(
        select(ConsensusRecord)
        .where(ConsensusRecord.id == record.id)
        .options(
            selectinload(ConsensusRecord.initiator),
            selectinload(ConsensusRecord.opinions).selectinload(ExpertOpinion.expert),
        )
    )
    record = result.scalar_one()
    log.info("Consensus initiated for case %s by %s", case_id, user.username)
    return _serialize_consensus(record)


@router.post("/{case_id}/consensus/opinion", status_code=status.HTTP_201_CREATED)
async def submit_opinion(
    case_id: UUID,
    body: ExpertOpinionCreate,
    db: DB,
    user: CurrentUser,
):
    """Expert: submit an opinion within an active consensus review."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin required", "code": "forbidden"},
        )

    if body.verdict not in VERDICTS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": f"Invalid verdict. Valid: {sorted(VERDICTS)}", "code": "validation_error"},
        )

    # Load consensus record
    result = await db.execute(
        select(ConsensusRecord)
        .where(ConsensusRecord.case_id == case_id)
        .options(
            selectinload(ConsensusRecord.initiator),
            selectinload(ConsensusRecord.opinions).selectinload(ExpertOpinion.expert),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "No consensus review for this case", "code": "not_found"},
        )
    if record.status != "open":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "detail": f"Consensus is not open (status: {record.status})",
                "code": "invalid_state",
            },
        )

    # Check for duplicate opinion
    existing_opinion = await db.execute(
        select(ExpertOpinion).where(
            ExpertOpinion.consensus_id == record.id,
            ExpertOpinion.expert_id == user.id,
        )
    )
    if existing_opinion.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "You have already submitted an opinion", "code": "conflict"},
        )

    opinion = ExpertOpinion(
        consensus_id=record.id,
        expert_id=user.id,
        verdict=body.verdict,
        confidence_level=body.confidence_level,
        summary=body.summary,
    )
    db.add(opinion)

    # Update tally
    tally = dict(record.verdict_tally or dict(_VERDICT_INIT))
    tally[body.verdict] = tally.get(body.verdict, 0) + 1
    record.verdict_tally = tally

    # Check if consensus is reached (≥50% majority)
    consensus_verdict, consensus_confidence = _derive_consensus(tally)
    if consensus_verdict:
        record.consensus_verdict = consensus_verdict
        record.consensus_confidence = consensus_confidence
        record.status = "reached"

        # Check for alignment — did this expert match the consensus?
        await award_reputation(
            db, user.id, "consensus_aligned",
            "consensus", record.id
        )

        await emit_audit_event(
            db, "consensus_reached", user.id, "case", case_id,
            {
                "verdict": consensus_verdict,
                "confidence": consensus_confidence,
                "tally": tally,
            }
        )
        log.info(
            "Consensus reached for case %s: %s (%s)",
            case_id, consensus_verdict, consensus_confidence
        )
    else:
        # Check for dissent from prior consensus direction
        if record.opinions:  # existing opinions exist
            prior_lead = max(tally, key=lambda k: tally[k])
            if body.verdict != prior_lead:
                await award_reputation(
                    db, user.id, "consensus_dissented",
                    "consensus", record.id
                )

    await db.flush()

    await emit_audit_event(
        db, "consensus_opinion_added", user.id, "case", case_id,
        {"verdict": body.verdict, "expert": user.username}
    )

    return {
        "opinion_id": str(opinion.id),
        "verdict": body.verdict,
        "current_tally": tally,
        "consensus_status": record.status,
        "consensus_verdict": record.consensus_verdict,
    }


@router.get("/{case_id}/consensus/opinions")
async def list_consensus_opinions(case_id: UUID, db: DB):
    """List all expert opinions in a consensus review."""
    result = await db.execute(
        select(ConsensusRecord)
        .where(ConsensusRecord.case_id == case_id)
        .options(
            selectinload(ConsensusRecord.initiator),
            selectinload(ConsensusRecord.opinions).selectinload(ExpertOpinion.expert),
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "No consensus review for this case", "code": "not_found"},
        )

    return {
        "consensus_id": str(record.id),
        "status": record.status,
        "verdict_tally": record.verdict_tally,
        "consensus_verdict": record.consensus_verdict,
        "opinions": [
            ExpertOpinionResponse(
                id=op.id,
                expert_username=op.expert.username,
                verdict=op.verdict,
                confidence_level=op.confidence_level,
                summary=op.summary,
                created_at=op.created_at,
            )
            for op in record.opinions
        ],
    }
