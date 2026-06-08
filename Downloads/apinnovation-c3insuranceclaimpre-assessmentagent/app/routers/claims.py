"""Claim API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_claim_service
from app.schemas.claim import ClaimResponse
from app.services.claim_service import ClaimService

router = APIRouter(tags=["Claims"])


@router.get("/claims", response_model=list[ClaimResponse])
async def list_claims(
    claim_service: ClaimService = Depends(get_claim_service),
) -> list[dict[str, Any]]:
    try:
        return claim_service.get_all_claims()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/claims/{claim_id}", response_model=ClaimResponse)
async def get_claim(
    claim_id: str,
    claim_service: ClaimService = Depends(get_claim_service),
) -> dict[str, Any]:
    try:
        claim = claim_service.get_claim_by_id(claim_id)
        if claim is None:
            raise HTTPException(
                status_code=404,
                detail=f"Claim '{claim_id}' not found",
            )
        return claim
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
