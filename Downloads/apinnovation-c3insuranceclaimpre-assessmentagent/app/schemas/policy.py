"""Policy-related response schemas."""

from pydantic import BaseModel


class PolicyResponse(BaseModel):
    policy_id: str
    policy_number: str
    policy_name: str
    insurance_type: str
    sum_insured: int
    policy_status: str


class ClauseResponse(BaseModel):
    clause_id: str
    insurance_type: str
    clause_type: str
    clause_name: str
    clause_text: str
