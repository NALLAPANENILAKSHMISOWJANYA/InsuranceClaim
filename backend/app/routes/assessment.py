"""
Insurance Claim Pre-Assurance – Assessment Router (Sprint 4)
Stub endpoints — full implementation in Sprint 4.
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/run/{claim_id}", summary="[Sprint 4] Run full pre-assessment pipeline")
def run_assessment(claim_id: str) -> dict:
    """Orchestrates OCR + RAG + validation + fraud → verdict. Implemented in Sprint 4."""
    return {"message": "Assessment engine will be implemented in Sprint 4.", "claim_id": claim_id}


@router.get("/{claim_id}", summary="[Sprint 4] Get assessment report for a claim")
def get_assessment(claim_id: str) -> dict:
    """Returns the latest assessment report for a claim. Implemented in Sprint 4."""
    return {"message": "Assessment retrieval will be implemented in Sprint 4.", "claim_id": claim_id}


@router.patch("/{claim_id}/adjuster-decision", summary="[Sprint 4] Human adjuster override")
def adjuster_decision(claim_id: str, payload: dict) -> dict:
    """Allows a human adjuster to override the engine verdict. Implemented in Sprint 4."""
    return {"message": "Adjuster override will be implemented in Sprint 4.", "claim_id": claim_id}
