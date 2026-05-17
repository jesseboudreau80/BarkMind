"""
Behavioral taxonomy routes.

Taxonomy terms are the extensible behavioral vocabulary used by experts
to annotate canine behavior with precision and consistency.
"""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DB
from app.models.taxonomy import TaxonomyTerm
from app.schemas.taxonomy import (
    AnnotationTaxonomyRefResponse,
    TaxonomyGroupedResponse,
    TaxonomyTermCreate,
    TaxonomyTermPatch,
    TaxonomyTermResponse,
)

log = logging.getLogger("barkmind.taxonomy")
router = APIRouter(prefix="/taxonomy", tags=["taxonomy"])


@router.get("", response_model=TaxonomyGroupedResponse)
async def list_taxonomy(
    db: DB,
    active_only: bool = Query(True, description="Return only active terms"),
    category: str | None = Query(None, description="Filter to a specific category"),
):
    """List all taxonomy terms grouped by category."""
    stmt = select(TaxonomyTerm).order_by(TaxonomyTerm.category, TaxonomyTerm.sort_order)
    if active_only:
        stmt = stmt.where(TaxonomyTerm.is_active == True)
    if category:
        stmt = stmt.where(TaxonomyTerm.category == category)

    result = await db.execute(stmt)
    terms = result.scalars().all()

    grouped: dict[str, list[TaxonomyTermResponse]] = {}
    for term in terms:
        cat = term.category
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(TaxonomyTermResponse.model_validate(term))

    return TaxonomyGroupedResponse(
        categories=grouped,
        total=len(terms),
    )


@router.get("/categories")
async def list_categories(db: DB):
    """Return the distinct set of taxonomy categories."""
    from sqlalchemy import distinct
    result = await db.execute(
        select(distinct(TaxonomyTerm.category))
        .where(TaxonomyTerm.is_active == True)
        .order_by(TaxonomyTerm.category)
    )
    return {"categories": [row[0] for row in result.fetchall()]}


@router.get("/{slug}", response_model=TaxonomyTermResponse)
async def get_term(slug: str, db: DB):
    """Get a single taxonomy term by slug."""
    result = await db.execute(select(TaxonomyTerm).where(TaxonomyTerm.slug == slug))
    term = result.scalar_one_or_none()
    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": f"Taxonomy term '{slug}' not found", "code": "not_found"},
        )
    return TaxonomyTermResponse.model_validate(term)


@router.post("", response_model=TaxonomyTermResponse, status_code=status.HTTP_201_CREATED)
async def create_term(body: TaxonomyTermCreate, db: DB, user: CurrentUser):
    """Create a new taxonomy term. Admin only."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin role required", "code": "forbidden"},
        )
    existing = await db.execute(select(TaxonomyTerm).where(TaxonomyTerm.slug == body.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": f"Slug '{body.slug}' already exists", "code": "conflict"},
        )
    term = TaxonomyTerm(**body.model_dump())
    db.add(term)
    await db.flush()
    log.info("Taxonomy term created: %s by %s", body.slug, user.username)
    return TaxonomyTermResponse.model_validate(term)


@router.patch("/{term_id}", response_model=TaxonomyTermResponse)
async def update_term(term_id: UUID, body: TaxonomyTermPatch, db: DB, user: CurrentUser):
    """Update a taxonomy term. Admin only."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin role required", "code": "forbidden"},
        )
    result = await db.execute(select(TaxonomyTerm).where(TaxonomyTerm.id == term_id))
    term = result.scalar_one_or_none()
    if term is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": "Term not found", "code": "not_found"},
        )
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(term, field, value)
    return TaxonomyTermResponse.model_validate(term)
