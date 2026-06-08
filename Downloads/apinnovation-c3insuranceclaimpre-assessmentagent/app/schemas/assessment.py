"""Assessment and system response schemas."""

from pydantic import BaseModel

from app.schemas.policy import ClauseResponse


class RootResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str


class AssessmentResponse(BaseModel):
    claim_id: str
    claimant_name: str | None
    policy_number: str
    claimed_amount: int | None
    policy_found: bool
    relevant_clauses: list[ClauseResponse]
    recommendation: str
    generated_by: str
