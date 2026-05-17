"""
Expert profile routes.

Experts are users with role='expert' or 'admin' who have created an ExpertProfile.
This router manages credential capture, verification, and public expert discovery.
"""
import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.expert_profile import ExpertProfile
from app.models.reputation_event import ReputationEvent
from app.models.user import User
from app.schemas.expert import (
    ExpertProfileCreate,
    ExpertProfilePatch,
    ExpertProfileResponse,
    ExpertStatsResponse,
    ExpertVerifyRequest,
)
from app.services.governance import emit_audit_event

log = logging.getLogger("barkmind.experts")
router = APIRouter(prefix="/experts", tags=["experts"])


def _serialize_profile(profile: ExpertProfile, user: User) -> ExpertProfileResponse:
    return ExpertProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        username=user.username,
        display_name=user.display_name,
        display_title=profile.display_title,
        organization=profile.organization,
        bio_professional=profile.bio_professional,
        years_experience=profile.years_experience,
        certifications=profile.certifications or [],
        specializations=profile.specializations or [],
        verification_status=profile.verification_status,
        verified_at=profile.verified_at,
        review_count=profile.review_count,
        annotation_count=profile.annotation_count,
        consensus_agreement_count=profile.consensus_agreement_count,
        reputation_score=user.reputation_score,
        created_at=profile.created_at,
    )


@router.get("")
async def list_experts(
    db: DB,
    verified_only: bool = Query(True),
    specialization: str | None = Query(None),
):
    """List expert profiles. Default: verified experts only."""
    stmt = (
        select(ExpertProfile)
        .options(selectinload(ExpertProfile.user))
        .order_by(ExpertProfile.review_count.desc())
    )
    if verified_only:
        stmt = stmt.where(ExpertProfile.verification_status == "verified")
    if specialization:
        stmt = stmt.where(
            ExpertProfile.specializations.contains([specialization])
        )

    result = await db.execute(stmt)
    profiles = result.scalars().all()
    return [_serialize_profile(p, p.user) for p in profiles]


@router.get("/me")
async def get_my_expert_profile(db: DB, user: CurrentUser):
    """Get the current user's expert profile (if it exists)."""
    result = await db.execute(
        select(ExpertProfile)
        .where(ExpertProfile.user_id == user.id)
        .options(selectinload(ExpertProfile.user))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Expert profile not found. Create one first.", "code": "not_found"},
        )
    return _serialize_profile(profile, user)


@router.post("/me", status_code=status.HTTP_201_CREATED)
async def create_expert_profile(body: ExpertProfileCreate, db: DB, user: CurrentUser):
    """Create an expert profile for the current user."""
    if user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Expert or admin role required", "code": "forbidden"},
        )

    existing = await db.execute(
        select(ExpertProfile).where(ExpertProfile.user_id == user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": "Expert profile already exists. Use PATCH to update.", "code": "conflict"},
        )

    profile = ExpertProfile(
        user_id=user.id,
        display_title=body.display_title,
        organization=body.organization,
        bio_professional=body.bio_professional,
        years_experience=body.years_experience,
        certifications=[c.model_dump() for c in body.certifications],
        specializations=body.specializations,
        verification_status="pending",
    )
    db.add(profile)
    await db.flush()

    await emit_audit_event(
        db, "expert_profile_created", user.id, "user", user.id,
        {"username": user.username}
    )

    result = await db.execute(
        select(ExpertProfile)
        .where(ExpertProfile.id == profile.id)
        .options(selectinload(ExpertProfile.user))
    )
    profile = result.scalar_one()
    log.info("Expert profile created: %s", user.username)
    return _serialize_profile(profile, user)


@router.patch("/me")
async def update_expert_profile(body: ExpertProfilePatch, db: DB, user: CurrentUser):
    """Update the current user's expert profile."""
    result = await db.execute(
        select(ExpertProfile)
        .where(ExpertProfile.user_id == user.id)
        .options(selectinload(ExpertProfile.user))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Expert profile not found", "code": "not_found"},
        )

    updates = body.model_dump(exclude_none=True)
    if "certifications" in updates:
        updates["certifications"] = [
            c if isinstance(c, dict) else c.model_dump()
            for c in updates["certifications"]
        ]
    for field, value in updates.items():
        setattr(profile, field, value)

    return _serialize_profile(profile, user)


@router.get("/{username}")
async def get_expert_profile(username: str, db: DB):
    """Get a public expert profile by username."""
    user_result = await db.execute(
        select(User).where(User.username == username, User.is_active == True)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "User not found", "code": "not_found"},
        )

    profile_result = await db.execute(
        select(ExpertProfile).where(ExpertProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "No expert profile for this user", "code": "not_found"},
        )
    return _serialize_profile(profile, user)


@router.patch("/{user_id}/verify")
async def verify_expert(
    user_id: UUID,
    body: ExpertVerifyRequest,
    db: DB,
    current_user: CurrentUser,
):
    """Admin: set verification status on an expert profile."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )

    result = await db.execute(
        select(ExpertProfile)
        .where(ExpertProfile.user_id == user_id)
        .options(selectinload(ExpertProfile.user))
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Expert profile not found", "code": "not_found"},
        )

    old_status = profile.verification_status
    profile.verification_status = body.verification_status
    if body.verification_status == "verified":
        profile.verified_by = current_user.id
        profile.verified_at = datetime.now(timezone.utc)

    await emit_audit_event(
        db, "expert_verified", current_user.id, "user", user_id,
        {"from": old_status, "to": body.verification_status, "username": profile.user.username}
    )

    if body.verification_status == "verified":
        from app.services.governance import award_reputation
        await award_reputation(db, user_id, "expert_verified", "expert_profile", profile.id)

    log.info("Expert %s verification: %s → %s", profile.user.username, old_status, body.verification_status)
    return _serialize_profile(profile, profile.user)


@router.get("/{username}/stats")
async def get_expert_stats(username: str, db: DB):
    """Public expert statistics."""
    user_result = await db.execute(
        select(User).where(User.username == username, User.is_active == True)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "User not found", "code": "not_found"},
        )

    profile_result = await db.execute(
        select(ExpertProfile).where(ExpertProfile.user_id == user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "No expert profile", "code": "not_found"},
        )

    return ExpertStatsResponse(
        username=user.username,
        reputation_score=user.reputation_score,
        review_count=profile.review_count,
        annotation_count=profile.annotation_count,
        consensus_agreement_count=profile.consensus_agreement_count,
        verification_status=profile.verification_status,
        specializations=profile.specializations or [],
    )
