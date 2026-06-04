"""
Insurance Claim Pre-Assurance – Analytics Router (Sprint 4)
Stub endpoints — full implementation in Sprint 4.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/summary", summary="[Sprint 4] Claim counts by status")
def summary() -> dict:
    """Returns total, pending, under_review, escalated, closed counts. Implemented in Sprint 4."""
    return {"message": "Analytics summary will be implemented in Sprint 4."}


@router.get("/avg-assessment-time", summary="[Sprint 4] Average time from claim creation to assessment")
def avg_assessment_time() -> dict:
    """Returns average minutes from claim creation to first assessment. Implemented in Sprint 4."""
    return {"message": "Avg assessment time will be implemented in Sprint 4."}


@router.get("/by-insurer", summary="[Sprint 4] Claim breakdown per insurer")
def by_insurer() -> dict:
    """Returns claim counts and amounts grouped by insurer. Implemented in Sprint 4."""
    return {"message": "Insurer breakdown will be implemented in Sprint 4."}


@router.get("/fraud-signals", summary="[Sprint 4] Top fraud signal frequencies")
def fraud_signal_summary() -> dict:
    """Returns most common fraud signal codes. Implemented in Sprint 4."""
    return {"message": "Fraud signal analytics will be implemented in Sprint 4."}
