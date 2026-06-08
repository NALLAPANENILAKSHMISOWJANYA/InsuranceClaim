"""Claim-related response schemas."""

from pydantic import BaseModel


class ClaimResponse(BaseModel):
    claim_id: str
    insurance_type: str
    claim_type: str
    policy_number: str
    claimant_name: str
    incident_date: str
    claimed_amount: int
    status: str
    queue_tier: str | None = None
    triage_score: int


class DashboardStatsResponse(BaseModel):
    total_claims: int
    health_claims: int
    vehicle_claims: int
    life_claims: int
    home_claims: int
    crop_claims: int
