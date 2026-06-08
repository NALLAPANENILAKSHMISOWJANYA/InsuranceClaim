"""
Insurance Claim Pre-Assurance – Fraud Detection Router (Sprint 3)
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.claim import Claim
from app.services import fraud_service
from app.utils.exceptions import ClaimNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/check/{claim_id}",
    summary="Run fraud signal checks on a claim",
    response_description="Full fraud result with risk level, score, and all signals",
)
def check_fraud(claim_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Runs all rule-based fraud signal checks against the claim and its documents.

    **Rules checked:**
    - `HIGH_VALUE` – amount exceeds ₹5 lakh threshold
    - `RAPID_RECLAIM` – prior claim on same policy within 90 days
    - `INSUFFICIENT_DOCS` – fewer than 2 documents uploaded
    - `MISSING_DISCHARGE_SUMMARY` – no discharge summary (health claims)
    - `MISSING_CLAIM_FORM` – no claim form uploaded
    - `OCR_FAILED_DOCS` – one or more documents failed text extraction
    - `WEEKEND_ADMISSION` – incident on Saturday or Sunday
    - `ROUND_AMOUNT` – suspiciously round claim amount (multiple of ₹10,000)
    - `DUPLICATE_POLICY_ACTIVE` – another PENDING claim on same policy number

    **Risk levels:** `CLEAR` → `LOW` → `MEDIUM` → `HIGH` → `CRITICAL`

    This endpoint is **read-only** — it does not modify the claim or create an
    assessment record. Use `POST /assessment/run/{claim_id}` to persist results.
    """
    # Validate claim exists
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise ClaimNotFoundError(claim_id)

    try:
        result = fraud_service.check(claim_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Fraud check failed for claim %s: %s", claim_id, exc)
        raise HTTPException(status_code=500, detail=f"Fraud check failed: {exc}")

    return result.to_dict()


@router.get(
    "/signals/{claim_id}",
    summary="Get fraud signals for a claim (re-runs checks)",
    response_description="List of individual fraud signals detected",
)
def get_fraud_signals(claim_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Returns only the signals list (without the full risk score breakdown).
    Useful for a quick signal summary in the adjuster UI.

    Re-runs the checks live — reflects the current state of uploaded documents.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise ClaimNotFoundError(claim_id)

    try:
        result = fraud_service.check(claim_id, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Fraud signals retrieval failed for claim %s: %s", claim_id, exc)
        raise HTTPException(status_code=500, detail=f"Fraud signals retrieval failed: {exc}")

    return {
        "claim_id": claim_id,
        "risk_level": result.risk_level,
        "signal_count": len(result.signals),
        "signals": [
            {
                "code": s.code,
                "severity": s.severity,
                "description": s.description,
                "detail": s.detail,
            }
            for s in result.signals
        ],
    }
