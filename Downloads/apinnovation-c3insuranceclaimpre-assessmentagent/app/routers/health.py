"""System health endpoints."""

from fastapi import APIRouter

from app.schemas.assessment import HealthResponse, RootResponse

router = APIRouter(tags=["System"])


@router.get("/", response_model=RootResponse)
async def root() -> RootResponse:
    return RootResponse(message="ClaimSense AI Running")


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="healthy")
