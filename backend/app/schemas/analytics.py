"""
Insurance Claim Pre-Assurance – Analytics Pydantic Schemas
"""
from pydantic import BaseModel


class ClaimsSummary(BaseModel):
    """High-level dashboard metrics."""
    total_claims: int
    pending: int
    under_review: int
    escalated: int
    closed: int


class AssessmentVerdictSummary(BaseModel):
    """Count of engine verdicts across all assessments."""
    approve: int
    reject: int
    escalate: int
    pending_review: int


class AvgAssessmentTime(BaseModel):
    """Average time (in minutes) from claim creation to first assessment."""
    avg_minutes: float


class InsurerBreakdown(BaseModel):
    """Claim counts grouped by insurer."""
    insurer: str
    total_claims: int
    total_amount: float


class FraudSignalSummary(BaseModel):
    """Frequency of each fraud signal code across all claims."""
    signal_code: str
    count: int
