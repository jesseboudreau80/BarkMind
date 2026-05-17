import os
import subprocess
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

APP_NAME = os.getenv("APP_NAME", "barkmind")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")
OWNER = os.getenv("OWNER", "jesse")
DOCTRINE_VERSION = os.getenv("DOCTRINE_VERSION", "2026-05-10")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8107"))
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3007"))

app = FastAPI(
    title="BarkMind API",
    description="Canine behavior intelligence platform",
    version=APP_VERSION,
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://barkmind.jesseboudreau.com", "http://127.0.0.1:3007"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


# ─── Governance Endpoints ─────────────────────────────────────────────────────

@app.get("/health", tags=["governance"])
def health():
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


@app.get("/whoami", tags=["governance"])
def whoami():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "port": BACKEND_PORT,
        "environment": ENVIRONMENT,
        "owner": OWNER,
        "aegis_connected": True,
    }


@app.get("/version", tags=["governance"])
def version():
    return {
        "version": APP_VERSION,
        "commit": _git_commit(),
        "built_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/.well-known/aegis-meta", tags=["governance"])
def aegis_meta():
    return {
        "app": APP_NAME,
        "description": "Canine behavior intelligence platform",
        "version": APP_VERSION,
        "owner": OWNER,
        "doctrine_version": DOCTRINE_VERSION,
        "runtime_mode": "production",
        "deployment_env": ENVIRONMENT,
        "backend_port": BACKEND_PORT,
        "frontend_port": FRONTEND_PORT,
        "lifecycle_support": True,
        "topology_registered": True,
    }
