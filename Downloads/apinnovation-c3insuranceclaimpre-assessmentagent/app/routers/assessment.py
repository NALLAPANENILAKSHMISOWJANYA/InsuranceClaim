"""Pre-assessment API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_assessment_service
from app.schemas.assessment import AssessmentResponse
from app.services.assessment_service import AssessmentService
from app.services.exceptions import ClaimNotFoundError

router = APIRouter(tags=["Assessment"])


@router.get("/pre-assessment/{claim_id}", response_model=AssessmentResponse)
async def pre_assessment(
    claim_id: str,
    assessment_service: AssessmentService = Depends(get_assessment_service),
) -> dict[str, Any]:
    try:
        return assessment_service.generate_pre_assessment(claim_id)
    except ClaimNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
