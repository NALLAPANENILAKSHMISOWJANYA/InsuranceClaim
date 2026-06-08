"""ClaimSense AI – Insurance Claim Pre-Assessment Agent API."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import PROJECT_ROOT, get_settings_for_data_dir
from app.constants import OPENAPI_TAGS
from app.dependencies import wire_services
from app.routers import assessment, claims, dashboard, health, policies, rag
from app.startup import validate_datasets

STATIC_DIR = PROJECT_ROOT / "app" / "static"

__all__ = ["app", "build_app", "validate_datasets", "PROJECT_ROOT"]


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan hook."""
    yield


def build_app(data_dir: Path | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings_for_data_dir(data_dir)
    validate_datasets(settings.data_dir)

    api = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="Insurance Claim Pre-Assessment Agent",
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
    )

    wire_services(api, settings)

    api.include_router(health.router)
    api.include_router(claims.router)
    api.include_router(policies.router)
    api.include_router(rag.router)
    api.include_router(assessment.router)
    api.include_router(dashboard.router)

    if STATIC_DIR.exists():
        api.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return api


app = build_app()
