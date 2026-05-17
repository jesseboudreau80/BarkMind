import logging
import os
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("barkmind")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("BarkMind backend starting — port %s", settings.backend_port)

    media_root = Path(settings.media_root)
    if not media_root.is_absolute():
        media_root = Path(__file__).parent.parent.parent / settings.media_root
    media_root.mkdir(parents=True, exist_ok=True)
    (media_root / "cases").mkdir(exist_ok=True)
    log.info("Media root: %s", media_root)

    from app.database import AsyncSessionLocal
    from app.seed import seed_tags
    from app.seed_taxonomy import seed_taxonomy
    async with AsyncSessionLocal() as db:
        added = await seed_tags(db)
        if added:
            log.info("Seeded %d behavioral tags", added)
        else:
            log.info("Tags already seeded")

    async with AsyncSessionLocal() as db:
        added = await seed_taxonomy(db)
        if added:
            log.info("Seeded %d behavioral taxonomy terms", added)
        else:
            log.info("Taxonomy already seeded")

    _mount_media(app, media_root)

    _register_with_aegis()

    log.info("BarkMind backend ready")
    yield
    log.info("BarkMind backend shutting down")


def _mount_media(app: FastAPI, media_root: Path) -> None:
    try:
        app.mount("/media", StaticFiles(directory=str(media_root)), name="media")
        log.info("Media served at /media")
    except Exception as exc:
        log.warning("Could not mount media directory: %s", exc)


def _register_with_aegis() -> None:
    payload = {
        "app_id": settings.app_name,
        "name": "BarkMind",
        "backend_port": settings.backend_port,
        "frontend_port": settings.frontend_port,
        "backend_url": f"http://127.0.0.1:{settings.backend_port}",
        "frontend_url": f"http://127.0.0.1:{settings.frontend_port}",
        "health_endpoint": f"http://127.0.0.1:{settings.backend_port}/health",
        "meta_endpoint": f"http://127.0.0.1:{settings.backend_port}/.well-known/aegis-meta",
        "lifecycle": ["start", "stop", "restart", "status"],
    }
    try:
        with httpx.Client(timeout=3) as client:
            r = client.post(
                f"{settings.aegis_base_url}/api/apps/register",
                json=payload,
                headers={"X-User-Email": settings.aegis_user_email},
            )
            log.info("Aegis registration: %s", r.status_code)
    except Exception as exc:
        log.warning("Aegis registration failed (Aegis may be offline): %s", exc)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


app = FastAPI(
    title="BarkMind API",
    description="Canine behavior intelligence platform",
    version=settings.app_version,
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://barkmind.jesseboudreau.com",
        f"http://127.0.0.1:{settings.frontend_port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_error"},
    )


# ─── Governance Endpoints ─────────────────────────────────────────────────────

@app.get("/health", tags=["governance"])
def health():
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


@app.get("/whoami", tags=["governance"])
def whoami():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "port": settings.backend_port,
        "environment": settings.environment,
        "owner": settings.owner,
        "aegis_connected": True,
    }


@app.get("/version", tags=["governance"])
def version():
    return {
        "version": settings.app_version,
        "commit": _git_commit(),
        "built_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/.well-known/aegis-meta", tags=["governance"])
def aegis_meta():
    return {
        "app": settings.app_name,
        "description": "Canine behavioral intelligence platform — expert review, annotation, and dataset governance",
        "version": settings.app_version,
        "owner": settings.owner,
        "doctrine_version": settings.doctrine_version,
        "runtime_mode": "production",
        "deployment_env": settings.environment,
        "backend_port": settings.backend_port,
        "frontend_port": settings.frontend_port,
        "lifecycle_support": True,
        "topology_registered": True,
        # Phase 6: capability declarations for Aegis
        "capabilities": [
            "behavioral_annotation",
            "expert_review",
            "multi_expert_consensus",
            "evidence_locking",
            "audit_trail",
            "dataset_export",
            "telemetry",
            "reputation_system",
            "taxonomy_management",
            "timeline_markers",
            "organization_support",
            "dataset_snapshots",
            "inter_rater_analysis",
        ],
        "governance_endpoints": {
            "status": "/governance/status",
            "metrics": "/governance/metrics",
            "telemetry_events": "/telemetry/events",
            "telemetry_summary": "/telemetry/summary",
            "analytics_summary": "/analytics/summary",
        },
    }


# ─── Routers ──────────────────────────────────────────────────────────────────

from app.routers import auth, cases, comments, media, tags, users
from app.routers import taxonomy, timeline  # Phase 4
from app.routers import experts, reviews, consensus, audit  # Phase 5
from app.routers import telemetry, analytics, exports, dataset, governance_ops  # Phase 6

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(cases.router)
app.include_router(comments.router)
app.include_router(tags.router)
app.include_router(media.router)
app.include_router(taxonomy.router)
app.include_router(timeline.router)
app.include_router(experts.router)
app.include_router(reviews.router)
app.include_router(consensus.router)
app.include_router(audit.router)
# Phase 6: operational intelligence
app.include_router(telemetry.router)
app.include_router(analytics.router)
app.include_router(exports.router)
app.include_router(dataset.router)
app.include_router(governance_ops.router)
app.include_router(governance_ops.org_router)
