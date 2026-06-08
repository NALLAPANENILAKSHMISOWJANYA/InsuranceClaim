"""Dashboard API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_claim_service
from app.schemas.claim import DashboardStatsResponse
from app.services.claim_service import ClaimService

router = APIRouter(tags=["Dashboard"])


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def dashboard_stats(
    claim_service: ClaimService = Depends(get_claim_service),
) -> dict[str, int]:
    try:
        return claim_service.get_dashboard_stats()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
