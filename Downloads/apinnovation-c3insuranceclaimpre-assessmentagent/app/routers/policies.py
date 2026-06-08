"""Policy API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_policy_service
from app.schemas.policy import PolicyResponse
from app.services.policy_service import PolicyService

router = APIRouter(tags=["Policies"])


@router.get("/policies/{policy_number}", response_model=PolicyResponse)
async def get_policy(
    policy_number: str,
    policy_service: PolicyService = Depends(get_policy_service),
) -> dict[str, Any]:
    try:
        policy = policy_service.get_policy_by_number(policy_number)
        if policy is None:
            raise HTTPException(
                status_code=404,
                detail=f"Policy '{policy_number}' not found",
            )
        return policy
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
