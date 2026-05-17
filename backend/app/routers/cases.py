from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB, OptionalUser
from app.models.annotation import Annotation
from app.models.case import Case
from app.models.case_tag import CaseTag
from app.models.comment import Comment
from app.models.resolution import ExpertResolution
from app.models.tag import Tag
from app.schemas.case import (
    AnnotationResponse,
    CaseCreate,
    CaseCreatedResponse,
    CaseDetail,
    CaseListItem,
    CaseListResponse,
    CasePatch,
    ResolutionResponse,
)
from app.schemas.media import MediaResponse
from app.schemas.tag import ApplyTagRequest, CaseTagResponse, TagResponse
from app.schemas.user import UserBrief

router = APIRouter(prefix="/cases", tags=["cases"])

_ALLOWED_STATUSES = {"open", "under_review", "resolved", "archived"}
_ALLOWED_SETTINGS = {"daycare", "shelter", "home", "grooming", "vet", "other"}
_ALLOWED_AGES = {"puppy", "adult", "senior"}


def _media_url(stored_path: str) -> str:
    return f"/media/{stored_path}"


def _build_case_detail(case: Case, comments_count: int) -> CaseDetail:
    tags = [
        CaseTagResponse(
            id=ct.id,
            tag=TagResponse.model_validate(ct.tag),
            confidence=ct.confidence,
            timestamp_note=ct.timestamp_note,
            applied_by_username=ct.applied_by_user.username,
            created_at=ct.created_at,
        )
        for ct in case.case_tags
    ]

    annotations = [
        AnnotationResponse(
            id=a.id,
            annotation_type=a.annotation_type,
            body=a.body,
            extra_data=a.extra_data or {},
            timestamp_start=a.timestamp_start,
            timestamp_end=a.timestamp_end,
            is_expert=a.is_expert,
            author_username=a.author.username,
            created_at=a.created_at,
            updated_at=a.updated_at,
        )
        for a in sorted(case.annotations, key=lambda x: (not x.is_expert, x.created_at))
    ]

    media = [
        MediaResponse(
            id=m.id,
            case_id=m.case_id,
            media_type=m.media_type,
            original_filename=m.original_filename,
            mime_type=m.mime_type,
            size_bytes=m.size_bytes,
            processing_status=m.processing_status,
            thumbnail_url=_media_url(m.thumbnail_path) if m.thumbnail_path else None,
            url=_media_url(m.stored_path),
            created_at=m.created_at,
        )
        for m in case.media
    ]

    resolution = None
    if case.expert_resolution:
        r = case.expert_resolution
        resolution = ResolutionResponse(
            id=r.id,
            verdict=r.verdict,
            summary=r.summary,
            recommendations=r.recommendations,
            confidence_level=r.confidence_level,
            expert_username=r.expert.username,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )

    return CaseDetail(
        id=case.id,
        title=case.title,
        description=case.description,
        status=case.status,
        setting=case.setting,
        subject_age_estimate=case.subject_age_estimate,
        subject_breed_note=case.subject_breed_note,
        trigger_context=case.trigger_context,
        species_context=case.species_context,
        submitter=UserBrief.model_validate(case.submitter),
        tags=tags,
        annotations=annotations,
        media=media,
        comments_count=comments_count,
        expert_resolution=resolution,
        ai_summary=case.ai_summary,
        view_count=case.view_count,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.get("", response_model=CaseListResponse)
async def list_cases(
    db: DB,
    user: OptionalUser,
    status: str | None = Query(None),
    tag: str | None = Query(None),
    setting: str | None = Query(None),
    search: str | None = Query(None),
    cursor: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    stmt = (
        select(Case)
        .where(Case.is_archived == False)
        .options(selectinload(Case.submitter))
        .order_by(Case.created_at.desc())
    )

    if status and status in _ALLOWED_STATUSES:
        stmt = stmt.where(Case.status == status)
    if setting and setting in _ALLOWED_SETTINGS:
        stmt = stmt.where(Case.setting == setting)
    if search:
        stmt = stmt.where(Case.title.ilike(f"%{search}%"))
    if tag:
        stmt = stmt.join(CaseTag, CaseTag.case_id == Case.id).join(
            Tag, Tag.id == CaseTag.tag_id
        ).where(Tag.slug == tag)
    if cursor:
        try:
            cursor_dt = datetime.fromisoformat(cursor)
            stmt = stmt.where(Case.created_at < cursor_dt)
        except ValueError:
            pass

    stmt = stmt.limit(limit + 1)
    result = await db.execute(stmt)
    cases = result.scalars().all()

    has_more = len(cases) > limit
    items = cases[:limit]
    next_cursor = items[-1].created_at.isoformat() if has_more and items else None

    return CaseListResponse(
        items=[
            CaseListItem(
                id=c.id,
                title=c.title,
                status=c.status,
                setting=c.setting,
                subject_age_estimate=c.subject_age_estimate,
                submitter=UserBrief.model_validate(c.submitter),
                view_count=c.view_count,
                created_at=c.created_at,
            )
            for c in items
        ],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.post("", response_model=CaseCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_case(body: CaseCreate, db: DB, user: CurrentUser):
    if body.setting and body.setting not in _ALLOWED_SETTINGS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": f"Invalid setting. Must be one of: {', '.join(_ALLOWED_SETTINGS)}", "code": "validation_error"},
        )
    if body.subject_age_estimate and body.subject_age_estimate not in _ALLOWED_AGES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"detail": f"Invalid age estimate. Must be one of: {', '.join(_ALLOWED_AGES)}", "code": "validation_error"},
        )

    case = Case(
        submitter_id=user.id,
        title=body.title,
        description=body.description,
        setting=body.setting,
        subject_age_estimate=body.subject_age_estimate,
        subject_breed_note=body.subject_breed_note,
        trigger_context=body.trigger_context,
        status="open",
    )
    db.add(case)
    await db.flush()

    return CaseCreatedResponse(id=case.id, status=case.status, created_at=case.created_at)


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(case_id: UUID, db: DB, user: OptionalUser):
    stmt = (
        select(Case)
        .where(Case.id == case_id, Case.is_archived == False)
        .options(
            selectinload(Case.submitter),
            selectinload(Case.media),
            selectinload(Case.case_tags).selectinload(CaseTag.tag),
            selectinload(Case.case_tags).selectinload(CaseTag.applied_by_user),
            selectinload(Case.annotations).selectinload(Annotation.author),
            selectinload(Case.expert_resolution).selectinload(ExpertResolution.expert),
        )
    )
    result = await db.execute(stmt)
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )

    count_result = await db.scalar(
        select(func.count()).where(Comment.case_id == case_id, Comment.is_archived == False)
    )

    case.view_count += 1

    return _build_case_detail(case, count_result or 0)


@router.patch("/{case_id}", response_model=CaseDetail)
async def patch_case(case_id: UUID, body: CasePatch, db: DB, user: CurrentUser):
    result = await db.execute(
        select(Case)
        .where(Case.id == case_id, Case.is_archived == False)
        .options(
            selectinload(Case.submitter),
            selectinload(Case.media),
            selectinload(Case.case_tags).selectinload(CaseTag.tag),
            selectinload(Case.case_tags).selectinload(CaseTag.applied_by_user),
            selectinload(Case.annotations).selectinload(Annotation.author),
            selectinload(Case.expert_resolution),
        )
    )
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )
    if case.submitter_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Not authorized to edit this case", "code": "forbidden"},
        )

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(case, field, value)

    count_result = await db.scalar(
        select(func.count()).where(Comment.case_id == case_id, Comment.is_archived == False)
    )
    return _build_case_detail(case, count_result or 0)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(case_id: UUID, db: DB, user: CurrentUser):
    result = await db.execute(select(Case).where(Case.id == case_id, Case.is_archived == False))
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Case not found", "code": "not_found"},
        )
    if case.submitter_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Not authorized to archive this case", "code": "forbidden"},
        )
    case.is_archived = True
    case.status = "archived"


# ─── Case Tags ────────────────────────────────────────────────────────────────

@router.get("/{case_id}/tags")
async def list_case_tags(case_id: UUID, db: DB):
    result = await db.execute(
        select(CaseTag)
        .where(CaseTag.case_id == case_id)
        .options(selectinload(CaseTag.tag), selectinload(CaseTag.applied_by_user))
    )
    case_tags = result.scalars().all()
    return [
        CaseTagResponse(
            id=ct.id,
            tag=TagResponse.model_validate(ct.tag),
            confidence=ct.confidence,
            timestamp_note=ct.timestamp_note,
            applied_by_username=ct.applied_by_user.username,
            created_at=ct.created_at,
        )
        for ct in case_tags
    ]


@router.post("/{case_id}/tags", status_code=status.HTTP_201_CREATED)
async def apply_tag(case_id: UUID, body: ApplyTagRequest, db: DB, user: CurrentUser):
    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    if case_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail={"detail": "Case not found", "code": "not_found"})

    tag_result = await db.execute(select(Tag).where(Tag.slug == body.tag_slug))
    tag = tag_result.scalar_one_or_none()
    if tag is None:
        raise HTTPException(status_code=404, detail={"detail": "Tag not found", "code": "not_found"})

    existing = await db.execute(
        select(CaseTag).where(
            CaseTag.case_id == case_id, CaseTag.tag_id == tag.id, CaseTag.applied_by == user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail={"detail": "You already applied this tag", "code": "conflict"},
        )

    case_tag = CaseTag(
        case_id=case_id,
        tag_id=tag.id,
        applied_by=user.id,
        confidence=body.confidence,
        timestamp_note=body.timestamp_note,
    )
    db.add(case_tag)
    await db.flush()
    return {"id": str(case_tag.id), "tag_slug": body.tag_slug, "applied": True}


@router.delete("/{case_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag(case_id: UUID, tag_id: UUID, db: DB, user: CurrentUser):
    result = await db.execute(
        select(CaseTag).where(CaseTag.id == tag_id, CaseTag.case_id == case_id)
    )
    ct = result.scalar_one_or_none()
    if ct is None:
        raise HTTPException(status_code=404, detail={"detail": "Tag application not found", "code": "not_found"})
    if ct.applied_by != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail={"detail": "Not authorized", "code": "forbidden"})
    await db.delete(ct)


# ─── Annotations (Phase 4 enhanced) ─────────────────────────────────────────

from app.schemas.annotation_enhanced import (
    EnhancedAnnotationCreate,
    EnhancedAnnotationPatch,
    EnhancedAnnotationResponse,
)
from app.services.annotation_service import (
    _build_annotation_response,
    attach_taxonomy_refs,
    capture_revision,
    load_annotation_with_refs,
)
from app.models.annotation_revision import AnnotationRevision
from app.models.annotation_taxonomy_ref import AnnotationTaxonomyRef

_ALLOWED_ANNOTATION_TYPES = {"observation", "interpretation", "concern", "recommendation"}
_ALLOWED_CONFIDENCE = {"high", "medium", "low"}


@router.get("/{case_id}/annotations")
async def list_annotations(
    case_id: UUID,
    db: DB,
    annotation_type: str | None = Query(None),
    confidence: str | None = Query(None),
    expert_only: bool = Query(False),
    has_taxonomy: bool = Query(False, description="Only return annotations with taxonomy refs"),
    timestamp_min: float | None = Query(None, description="Filter by timestamp_start >= value"),
    timestamp_max: float | None = Query(None, description="Filter by timestamp_start <= value"),
):
    """
    List annotations for a case with optional filtering.

    Filters: annotation_type, confidence, expert_only, has_taxonomy, timestamp range.
    Returns: expert annotations first, then chronological.
    """
    stmt = (
        select(Annotation)
        .where(Annotation.case_id == case_id)
        .options(
            selectinload(Annotation.author),
            selectinload(Annotation.taxonomy_refs).selectinload(AnnotationTaxonomyRef.term),
            selectinload(Annotation.revisions),
        )
        .order_by(Annotation.is_expert.desc(), Annotation.created_at.asc())
    )
    if annotation_type and annotation_type in _ALLOWED_ANNOTATION_TYPES:
        stmt = stmt.where(Annotation.annotation_type == annotation_type)
    if confidence and confidence in _ALLOWED_CONFIDENCE:
        stmt = stmt.where(Annotation.confidence_level == confidence)
    if expert_only:
        stmt = stmt.where(Annotation.is_expert == True)
    if has_taxonomy:
        from sqlalchemy import exists as sql_exists
        stmt = stmt.where(
            sql_exists().where(AnnotationTaxonomyRef.annotation_id == Annotation.id)
        )
    if timestamp_min is not None:
        stmt = stmt.where(Annotation.timestamp_start >= timestamp_min)
    if timestamp_max is not None:
        stmt = stmt.where(Annotation.timestamp_start <= timestamp_max)

    result = await db.execute(stmt)
    annotations = result.scalars().all()

    return [
        _build_annotation_response(a, revision_count=len(a.revisions))
        for a in annotations
    ]


@router.post("/{case_id}/annotations", status_code=status.HTTP_201_CREATED)
async def add_annotation(
    case_id: UUID,
    body: EnhancedAnnotationCreate,
    db: DB,
    user: CurrentUser,
):
    """
    Add a structured behavioral annotation to a case.

    Supports: annotation type, body text, confidence level, timestamp range,
    taxonomy term references, and extensible extra_data.
    """
    if body.annotation_type not in _ALLOWED_ANNOTATION_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "detail": f"Invalid annotation_type. Must be one of: {', '.join(sorted(_ALLOWED_ANNOTATION_TYPES))}",
                "code": "validation_error",
            },
        )
    if body.confidence_level and body.confidence_level not in _ALLOWED_CONFIDENCE:
        raise HTTPException(
            status_code=422,
            detail={"detail": "confidence_level must be high, medium, or low", "code": "validation_error"},
        )

    case_result = await db.execute(
        select(Case).where(Case.id == case_id, Case.is_archived == False)
    )
    if case_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404, detail={"detail": "Case not found", "code": "not_found"}
        )

    annotation = Annotation(
        case_id=case_id,
        author_id=user.id,
        annotation_type=body.annotation_type,
        body=body.body,
        extra_data=body.extra_data,
        media_id=body.media_id,
        timestamp_start=body.timestamp_start,
        timestamp_end=body.timestamp_end,
        is_expert=user.role in ("expert", "admin"),
        confidence_level=body.confidence_level,
    )
    db.add(annotation)
    await db.flush()

    # Attach taxonomy term references
    if body.taxonomy_term_slugs:
        await attach_taxonomy_refs(db, annotation, body.taxonomy_term_slugs)

    await db.flush()
    return {"id": str(annotation.id), "created": True}


@router.patch("/{case_id}/annotations/{annotation_id}")
async def edit_annotation(
    case_id: UUID,
    annotation_id: UUID,
    body: EnhancedAnnotationPatch,
    db: DB,
    user: CurrentUser,
):
    """
    Edit an annotation with automatic revision capture.

    The previous state is saved as an immutable AnnotationRevision before
    any changes are applied, providing a complete audit trail.
    """
    result = await db.execute(
        select(Annotation)
        .where(Annotation.id == annotation_id, Annotation.case_id == case_id)
        .options(
            selectinload(Annotation.author),
            selectinload(Annotation.taxonomy_refs).selectinload(AnnotationTaxonomyRef.term),
            selectinload(Annotation.revisions),
        )
    )
    annotation = result.scalar_one_or_none()
    if annotation is None:
        raise HTTPException(
            status_code=404, detail={"detail": "Annotation not found", "code": "not_found"}
        )
    if annotation.author_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=403, detail={"detail": "Not authorized", "code": "forbidden"}
        )
    if body.confidence_level and body.confidence_level not in _ALLOWED_CONFIDENCE:
        raise HTTPException(
            status_code=422,
            detail={"detail": "confidence_level must be high, medium, or low", "code": "validation_error"},
        )

    # Capture revision BEFORE applying changes
    await capture_revision(db, annotation, user.id, body.change_reason)

    # Apply updates
    if body.body is not None:
        annotation.body = body.body
    if body.annotation_type is not None:
        if body.annotation_type not in _ALLOWED_ANNOTATION_TYPES:
            raise HTTPException(status_code=422, detail={"detail": "Invalid annotation_type", "code": "validation_error"})
        annotation.annotation_type = body.annotation_type
    if body.confidence_level is not None:
        annotation.confidence_level = body.confidence_level
    if body.extra_data is not None:
        annotation.extra_data = body.extra_data

    return _build_annotation_response(
        annotation, revision_count=len(annotation.revisions) + 1
    )


@router.delete("/{case_id}/annotations/{annotation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    case_id: UUID,
    annotation_id: UUID,
    db: DB,
    user: CurrentUser,
):
    """Delete an annotation. Author or admin only."""
    result = await db.execute(
        select(Annotation).where(
            Annotation.id == annotation_id, Annotation.case_id == case_id
        )
    )
    annotation = result.scalar_one_or_none()
    if annotation is None:
        raise HTTPException(
            status_code=404, detail={"detail": "Annotation not found", "code": "not_found"}
        )
    if annotation.author_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=403, detail={"detail": "Not authorized", "code": "forbidden"}
        )
    await db.delete(annotation)


@router.get("/{case_id}/annotations/{annotation_id}/revisions")
async def get_annotation_revisions(
    case_id: UUID,
    annotation_id: UUID,
    db: DB,
    user: CurrentUser,
):
    """Return the edit revision history for an annotation (author/expert/admin)."""
    ann_result = await db.execute(
        select(Annotation).where(
            Annotation.id == annotation_id, Annotation.case_id == case_id
        )
    )
    if ann_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=404, detail={"detail": "Annotation not found", "code": "not_found"}
        )

    rev_result = await db.execute(
        select(AnnotationRevision)
        .where(AnnotationRevision.annotation_id == annotation_id)
        .options(selectinload(AnnotationRevision.editor))
        .order_by(AnnotationRevision.created_at.desc())
    )
    revisions = rev_result.scalars().all()

    return [
        {
            "id": str(r.id),
            "revised_by_username": r.editor.username,
            "previous_body": r.previous_body,
            "previous_annotation_type": r.previous_annotation_type,
            "previous_confidence_level": r.previous_confidence_level,
            "change_reason": r.change_reason,
            "created_at": r.created_at.isoformat(),
        }
        for r in revisions
    ]


@router.post("/{case_id}/annotations/{annotation_id}/taxonomy")
async def add_taxonomy_ref(
    case_id: UUID,
    annotation_id: UUID,
    db: DB,
    user: CurrentUser,
    slug: str = Query(..., description="Taxonomy term slug to attach"),
):
    """Add a taxonomy term reference to an existing annotation."""
    result = await db.execute(
        select(Annotation)
        .where(Annotation.id == annotation_id, Annotation.case_id == case_id)
        .options(selectinload(Annotation.taxonomy_refs))
    )
    annotation = result.scalar_one_or_none()
    if annotation is None:
        raise HTTPException(
            status_code=404, detail={"detail": "Annotation not found", "code": "not_found"}
        )
    if annotation.author_id != user.id and user.role not in ("expert", "admin"):
        raise HTTPException(
            status_code=403, detail={"detail": "Not authorized", "code": "forbidden"}
        )

    await attach_taxonomy_refs(db, annotation, [slug])
    return {"attached": True, "slug": slug}


@router.delete(
    "/{case_id}/annotations/{annotation_id}/taxonomy/{ref_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_taxonomy_ref(
    case_id: UUID,
    annotation_id: UUID,
    ref_id: UUID,
    db: DB,
    user: CurrentUser,
):
    """Remove a taxonomy term reference from an annotation."""
    result = await db.execute(
        select(AnnotationTaxonomyRef).where(
            AnnotationTaxonomyRef.id == ref_id,
            AnnotationTaxonomyRef.annotation_id == annotation_id,
        )
    )
    ref = result.scalar_one_or_none()
    if ref is None:
        raise HTTPException(
            status_code=404, detail={"detail": "Taxonomy reference not found", "code": "not_found"}
        )
    await db.delete(ref)


# ─── Expert Resolution ────────────────────────────────────────────────────────

class ResolutionCreate(BaseModel):
    verdict: str
    summary: str
    recommendations: str | None = None
    confidence_level: str | None = None


_ALLOWED_VERDICTS = {"safe", "concern", "escalation_risk", "requires_intervention"}
_ALLOWED_CONFIDENCE = {"high", "medium", "low"}


@router.get("/{case_id}/resolution")
async def get_resolution(case_id: UUID, db: DB):
    result = await db.execute(
        select(ExpertResolution)
        .where(ExpertResolution.case_id == case_id)
        .options(selectinload(ExpertResolution.expert))
    )
    resolution = result.scalar_one_or_none()
    if resolution is None:
        raise HTTPException(status_code=404, detail={"detail": "No resolution yet", "code": "not_found"})
    return ResolutionResponse(
        id=resolution.id,
        verdict=resolution.verdict,
        summary=resolution.summary,
        recommendations=resolution.recommendations,
        confidence_level=resolution.confidence_level,
        expert_username=resolution.expert.username,
        created_at=resolution.created_at,
        updated_at=resolution.updated_at,
    )


@router.post("/{case_id}/resolution", status_code=status.HTTP_201_CREATED)
async def create_resolution(
    case_id: UUID,
    body: ResolutionCreate,
    db: DB,
    user: CurrentUser,
):
    if user.role not in ("expert", "admin"):
        raise HTTPException(status_code=403, detail={"detail": "Expert or admin role required", "code": "forbidden"})
    if body.verdict not in _ALLOWED_VERDICTS:
        raise HTTPException(status_code=422, detail={"detail": f"Invalid verdict", "code": "validation_error"})
    if body.confidence_level and body.confidence_level not in _ALLOWED_CONFIDENCE:
        raise HTTPException(status_code=422, detail={"detail": "Invalid confidence_level", "code": "validation_error"})

    case_result = await db.execute(select(Case).where(Case.id == case_id, Case.is_archived == False))
    case = case_result.scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=404, detail={"detail": "Case not found", "code": "not_found"})

    existing = await db.execute(select(ExpertResolution).where(ExpertResolution.case_id == case_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"detail": "Resolution already exists. Use PATCH to update.", "code": "conflict"})

    resolution = ExpertResolution(
        case_id=case_id,
        expert_id=user.id,
        verdict=body.verdict,
        summary=body.summary,
        recommendations=body.recommendations,
        confidence_level=body.confidence_level,
    )
    db.add(resolution)
    case.status = "resolved"
    await db.flush()

    # Emit governance events
    from app.services.governance import award_reputation, emit_audit_event
    await emit_audit_event(
        db, "resolution_submitted", user.id, "case", case_id,
        {"verdict": body.verdict, "expert": user.username}
    )
    await award_reputation(db, user.id, "resolution_submitted", "case", case_id)

    # Update expert profile review count if profile exists
    from app.models.expert_profile import ExpertProfile
    ep_result = await db.execute(select(ExpertProfile).where(ExpertProfile.user_id == user.id))
    ep = ep_result.scalar_one_or_none()
    if ep:
        ep.review_count += 1

    return {"id": str(resolution.id), "verdict": resolution.verdict}


@router.patch("/{case_id}/resolution")
async def update_resolution(
    case_id: UUID,
    body: ResolutionCreate,
    db: DB,
    user: CurrentUser,
):
    if user.role not in ("expert", "admin"):
        raise HTTPException(status_code=403, detail={"detail": "Expert or admin role required", "code": "forbidden"})

    result = await db.execute(
        select(ExpertResolution)
        .where(ExpertResolution.case_id == case_id)
        .options(selectinload(ExpertResolution.expert))
    )
    resolution = result.scalar_one_or_none()
    if resolution is None:
        raise HTTPException(status_code=404, detail={"detail": "No resolution to update", "code": "not_found"})

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(resolution, field, value)

    return ResolutionResponse(
        id=resolution.id,
        verdict=resolution.verdict,
        summary=resolution.summary,
        recommendations=resolution.recommendations,
        confidence_level=resolution.confidence_level,
        expert_username=resolution.expert.username,
        created_at=resolution.created_at,
        updated_at=resolution.updated_at,
    )
