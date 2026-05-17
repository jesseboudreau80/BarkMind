"""
Annotation business logic for Phase 4.

Handles:
- Creating annotations with taxonomy refs
- Editing annotations with revision capture
- Filtering annotation lists
- Building enriched response objects
"""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.annotation import Annotation
from app.models.annotation_revision import AnnotationRevision
from app.models.annotation_taxonomy_ref import AnnotationTaxonomyRef
from app.models.taxonomy import TaxonomyTerm
from app.schemas.annotation_enhanced import EnhancedAnnotationResponse, AnnotationTaxonomyRefOut
from app.schemas.taxonomy import TaxonomyTermResponse

log = logging.getLogger("barkmind.annotations")


def _build_annotation_response(
    annotation: Annotation,
    revision_count: int = 0,
) -> EnhancedAnnotationResponse:
    """Build a rich annotation response from a loaded ORM object."""
    taxonomy_refs = []
    if annotation.taxonomy_refs:
        for ref in annotation.taxonomy_refs:
            taxonomy_refs.append(
                AnnotationTaxonomyRefOut(
                    id=ref.id,
                    taxonomy_term_id=ref.taxonomy_term_id,
                    term=TaxonomyTermResponse.model_validate(ref.term),
                    created_at=ref.created_at,
                )
            )

    return EnhancedAnnotationResponse(
        id=annotation.id,
        annotation_type=annotation.annotation_type,
        body=annotation.body,
        extra_data=annotation.extra_data or {},
        timestamp_start=annotation.timestamp_start,
        timestamp_end=annotation.timestamp_end,
        is_expert=annotation.is_expert,
        confidence_level=annotation.confidence_level,
        author_username=annotation.author.username,
        taxonomy_refs=taxonomy_refs,
        revision_count=revision_count,
        created_at=annotation.created_at,
        updated_at=annotation.updated_at,
    )


async def load_annotation_with_refs(
    db: AsyncSession,
    annotation_id: UUID,
) -> Annotation | None:
    """Load an annotation with all Phase 4 relationships."""
    result = await db.execute(
        select(Annotation)
        .where(Annotation.id == annotation_id)
        .options(
            selectinload(Annotation.author),
            selectinload(Annotation.taxonomy_refs).selectinload(AnnotationTaxonomyRef.term),
            selectinload(Annotation.revisions),
        )
    )
    return result.scalar_one_or_none()


async def resolve_taxonomy_slugs(
    db: AsyncSession,
    slugs: list[str],
) -> list[TaxonomyTerm]:
    """Resolve taxonomy term slugs to ORM objects. Skips unknown slugs."""
    if not slugs:
        return []
    result = await db.execute(
        select(TaxonomyTerm).where(
            TaxonomyTerm.slug.in_(slugs),
            TaxonomyTerm.is_active == True,
        )
    )
    return result.scalars().all()


async def attach_taxonomy_refs(
    db: AsyncSession,
    annotation: Annotation,
    taxonomy_slugs: list[str],
) -> None:
    """
    Add taxonomy term references to an annotation.

    Skips slugs that are already referenced.
    Unknown slugs are silently skipped (not an error).
    """
    if not taxonomy_slugs:
        return

    terms = await resolve_taxonomy_slugs(db, taxonomy_slugs)
    if not terms:
        return

    # Query existing refs directly — avoids lazy='raise' on the relationship
    existing_result = await db.execute(
        select(AnnotationTaxonomyRef.taxonomy_term_id).where(
            AnnotationTaxonomyRef.annotation_id == annotation.id
        )
    )
    existing_term_ids = {row[0] for row in existing_result.fetchall()}

    for term in terms:
        if term.id not in existing_term_ids:
            ref = AnnotationTaxonomyRef(
                annotation_id=annotation.id,
                taxonomy_term_id=term.id,
            )
            db.add(ref)


async def capture_revision(
    db: AsyncSession,
    annotation: Annotation,
    editor_id: UUID,
    change_reason: str | None = None,
) -> None:
    """
    Snapshot the current annotation state as an immutable revision record.

    Call this BEFORE applying updates to the annotation.
    """
    revision = AnnotationRevision(
        annotation_id=annotation.id,
        revised_by=editor_id,
        previous_body=annotation.body,
        previous_annotation_type=annotation.annotation_type,
        previous_confidence_level=annotation.confidence_level,
        previous_extra_data=annotation.extra_data,
        change_reason=change_reason,
    )
    db.add(revision)
    log.info("Captured revision for annotation %s by user %s", annotation.id, editor_id)
