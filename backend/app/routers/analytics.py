"""
Analytics routes — aggregate platform intelligence.

All analytics are read-only SQL aggregations.
No AI inference, no predictive scoring.
Pure operational data for human decision making.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUser, DB
from app.services.analytics_service import (
    annotation_analytics,
    case_analytics,
    consensus_analytics,
    expert_analytics,
    platform_metrics,
    taxonomy_analytics,
)

log = logging.getLogger("barkmind.analytics")
router = APIRouter(prefix="/analytics", tags=["analytics"])


def _require_admin(user: CurrentUser) -> None:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"detail": "Admin required", "code": "forbidden"},
        )


@router.get("/cases")
async def get_case_analytics(db: DB, user: CurrentUser):
    """Case velocity, status distribution, setting breakdown, resolution rates."""
    _require_admin(user)
    return await case_analytics(db)


@router.get("/annotations")
async def get_annotation_analytics(db: DB, user: CurrentUser):
    """Annotation volume, type distribution, taxonomy adoption, top terms."""
    _require_admin(user)
    return await annotation_analytics(db)


@router.get("/experts")
async def get_expert_analytics(db: DB, user: CurrentUser):
    """Expert participation, review throughput, stale review detection."""
    _require_admin(user)
    return await expert_analytics(db)


@router.get("/taxonomy")
async def get_taxonomy_analytics(db: DB, user: CurrentUser):
    """Taxonomy term adoption, category usage heatmap, unused terms."""
    _require_admin(user)
    return await taxonomy_analytics(db)


@router.get("/consensus")
async def get_consensus_analytics(db: DB, user: CurrentUser):
    """Consensus agreement rates, dispute frequency, verdict distribution."""
    _require_admin(user)
    return await consensus_analytics(db)


@router.get("/summary")
async def get_analytics_summary(db: DB, user: CurrentUser):
    """Full platform metrics summary — combines all analytics in one call."""
    _require_admin(user)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": await platform_metrics(db),
        "cases": await case_analytics(db),
        "annotations": await annotation_analytics(db),
        "experts": await expert_analytics(db),
        "taxonomy": await taxonomy_analytics(db),
        "consensus": await consensus_analytics(db),
    }


@router.get("/inter_rater")
async def get_inter_rater_foundations(db: DB, user: CurrentUser):
    """
    Inter-rater reliability foundation data.

    Returns the raw opinion data needed to compute Cohen's kappa and
    Krippendorff's alpha for expert annotation agreement.

    This is structured data for external computation — not a computed score.
    """
    _require_admin(user)

    from app.models.consensus import ConsensusRecord, ExpertOpinion
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(ConsensusRecord)
        .where(ConsensusRecord.status == "reached")
        .options(
            selectinload(ConsensusRecord.opinions).selectinload(ExpertOpinion.expert)
        )
        .limit(1000)
    )
    records = result.scalars().all()

    # Format as comparison pairs for IRR calculation
    comparison_data = []
    for r in records:
        if len(r.opinions) >= 2:
            comparison_data.append({
                "case_id": str(r.case_id),
                "consensus_verdict": r.consensus_verdict,
                "opinions": [
                    {"expert": op.expert.username, "verdict": op.verdict}
                    for op in r.opinions
                ],
                "agreement": len(set(op.verdict for op in r.opinions)) == 1,
            })

    total = len(comparison_data)
    unanimous = sum(1 for c in comparison_data if c["agreement"])

    return {
        "total_multi_expert_cases": total,
        "unanimous_agreement_count": unanimous,
        "unanimous_agreement_rate": round((unanimous / total * 100) if total > 0 else 0, 1),
        "cases": comparison_data[:100],  # First 100 for API response
        "note": "Use full export for complete IRR computation (POST /exports/consensus)",
    }
