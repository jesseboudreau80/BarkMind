"""
Review workflow service — case state transitions and assignment logic.

State machine:
  intake → open → under_review → expert_review → consensus_pending → resolved → locked
                                              ↘ escalated ↗
                           ↘ archived (from any non-locked state, admin only)

This service validates transitions and builds the case state snapshot.
"""
import logging
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.annotation import Annotation
from app.models.case import Case
from app.models.case_media import CaseMedia
from app.models.case_tag import CaseTag
from app.models.resolution import ExpertResolution

log = logging.getLogger("barkmind.review")

# Valid case statuses including Phase 5 additions
ALL_CASE_STATUSES = {
    "intake",
    "open",
    "under_review",
    "expert_review",
    "consensus_pending",
    "escalated",
    "resolved",
    "locked",
    "archived",
}

# Valid state transitions: {from_state: {to_states}}
VALID_TRANSITIONS: dict[str, set[str]] = {
    "intake": {"open", "archived"},
    "open": {"under_review", "expert_review", "archived"},
    "under_review": {"expert_review", "resolved", "archived"},
    "expert_review": {"consensus_pending", "resolved", "escalated", "archived"},
    "consensus_pending": {"resolved", "escalated"},
    "escalated": {"expert_review", "resolved"},
    "resolved": {"locked", "archived"},
    "locked": set(),  # admin can force-unlock, handled separately
    "archived": set(),
}


def can_transition(from_status: str, to_status: str, is_admin: bool = False) -> bool:
    """Check if a state transition is valid."""
    if is_admin and to_status == "archived":
        return True
    if is_admin and from_status == "locked":
        return to_status in {"resolved"}  # admin unlock
    valid = VALID_TRANSITIONS.get(from_status, set())
    return to_status in valid


async def build_case_snapshot(db: AsyncSession, case_id: UUID) -> dict:
    """
    Build an immutable snapshot of a case's current state.

    Used when locking evidence — captures the complete reviewable state.
    """
    case_result = await db.execute(
        select(Case)
        .where(Case.id == case_id)
        .options(selectinload(Case.submitter))
    )
    case = case_result.scalar_one_or_none()
    if not case:
        return {}

    annotation_count = await db.scalar(
        select(func.count()).where(Annotation.case_id == case_id)
    ) or 0

    tag_count = await db.scalar(
        select(func.count()).where(CaseTag.case_id == case_id)
    ) or 0

    media_count = await db.scalar(
        select(func.count()).where(CaseMedia.case_id == case_id)
    ) or 0

    resolution_result = await db.execute(
        select(ExpertResolution)
        .where(ExpertResolution.case_id == case_id)
        .options(selectinload(ExpertResolution.expert))
    )
    resolution = resolution_result.scalar_one_or_none()

    snapshot: dict = {
        "case_id": str(case_id),
        "title": case.title,
        "status_at_lock": case.status,
        "submitter": case.submitter.username,
        "setting": case.setting,
        "subject_age_estimate": case.subject_age_estimate,
        "annotation_count": annotation_count,
        "tag_count": tag_count,
        "media_count": media_count,
        "created_at": case.created_at.isoformat(),
    }

    if resolution:
        snapshot["resolution"] = {
            "verdict": resolution.verdict,
            "confidence_level": resolution.confidence_level,
            "expert": resolution.expert.username,
            "submitted_at": resolution.created_at.isoformat(),
        }

    return snapshot


async def is_case_locked(db: AsyncSession, case_id: UUID) -> bool:
    """Check if a case has an active evidence lock."""
    from app.models.evidence_lock import EvidenceLock
    result = await db.execute(
        select(EvidenceLock.id).where(EvidenceLock.case_id == case_id)
    )
    return result.scalar_one_or_none() is not None
