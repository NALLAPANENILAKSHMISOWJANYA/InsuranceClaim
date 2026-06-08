"""RAG search API endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_policy_service
from app.schemas.policy import ClauseResponse
from app.services.policy_service import PolicyService

router = APIRouter(tags=["RAG"])


@router.get("/rag/search", response_model=list[ClauseResponse])
async def rag_search(
    q: str = Query(..., min_length=1),
    policy_service: PolicyService = Depends(get_policy_service),
) -> list[dict[str, Any]]:
    try:
        return policy_service.search_clauses(query=q)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
