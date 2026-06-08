"""
Insurance Claim Pre-Assurance – Assessment Pydantic Schemas
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Verdict(str, Enum):
    """Pre-assessment engine verdicts. Advisory only — human adjuster decides final outcome."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"
    PENDING_REVIEW = "PENDING_REVIEW"


class PolicyChecks(BaseModel):
    """Structured results of individual policy validation checks."""
    coverage_eligible: Optional[bool] = None
    waiting_period_cleared: Optional[bool] = None
    ped_conflict: Optional[bool] = None
    room_rent_within_limit: Optional[bool] = None


class FraudSignal(BaseModel):
    """A single fraud signal raised by the rule engine."""
    signal_code: str
    severity: str   # "HIGH" | "MEDIUM" | "LOW"
    description: str


class AssessmentResponse(BaseModel):
    """Full assessment report returned by the assessment engine."""
    model_config = {"from_attributes": True}

    id: str
    claim_id: str
    verdict: str
    confidence_score: Optional[float]
    reasoning: Optional[str]
    policy_checks: PolicyChecks
    fraud_signals: list[FraudSignal]
    missing_documents: list[str]
    policy_chunks_used: list[dict[str, Any]]
    adjuster_override: Optional[str]
    adjuster_notes: Optional[str]
    adjuster_reviewed_at: Optional[datetime]
    assessed_at: datetime


class AdjusterDecision(BaseModel):
    """Payload for a human adjuster to override the engine verdict."""
    override_verdict: Verdict
    notes: str = Field(..., min_length=10, max_length=2000)
