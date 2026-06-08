"""Pre-assessment business workflows."""

from __future__ import annotations

from typing import Any

from app.constants import (
    AUDIT_ACTOR_SYSTEM,
    AUDIT_EVENT_TYPE_PRE_ASSESSMENT,
    GENERATED_BY,
    RECOMMENDATION_REVIEW_REQUIRED,
)
from app.domain.rag.retriever import RAGRetriever
from app.services.audit_service import AuditService
from app.services.claim_service import ClaimService
from app.services.exceptions import ClaimNotFoundError
from app.services.policy_service import PolicyService


class AssessmentService:
    """Generates structured pre-assessments for human review."""

    def __init__(
        self,
        claim_service: ClaimService,
        policy_service: PolicyService,
        audit_service: AuditService,
    ) -> None:
        self._claim_service = claim_service
        self._policy_service = policy_service
        self._audit_service = audit_service

    @staticmethod
    def _build_clause_query(claim: dict[str, Any]) -> str:
        """Build a keyword query from claim attributes."""
        claim_type = str(claim.get("claim_type", "")).replace("_", " ")
        insurance_type = str(claim.get("insurance_type", ""))
        return f"{insurance_type} {claim_type}".strip()

    def generate_pre_assessment(self, claim_id: str) -> dict[str, Any]:
        """
        Generate a pre-assessment for a claim.

        Flow: claim -> policy -> relevant clauses -> structured response.
        Always recommends REVIEW_REQUIRED for human adjudication.
        """
        claim = self._claim_service.get_claim_by_id(claim_id)
        if claim is None:
            raise ClaimNotFoundError(claim_id)

        policy_number = str(claim["policy_number"])
        policy = self._policy_service.get_policy_by_number(policy_number)
        insurance_type = str(claim.get("insurance_type", ""))

        clause_query = self._build_clause_query(claim)
        retriever = RAGRetriever(self._policy_service.get_policy_clauses())
        relevant_clauses = retriever.search_by_insurance_type(
            query=clause_query,
            insurance_type=insurance_type,
        )

        assessment = {
            "claim_id": claim_id,
            "claimant_name": claim.get("claimant_name"),
            "policy_number": policy_number,
            "claimed_amount": claim.get("claimed_amount"),
            "policy_found": policy is not None,
            "relevant_clauses": relevant_clauses,
            "recommendation": RECOMMENDATION_REVIEW_REQUIRED,
            "generated_by": GENERATED_BY,
        }

        self._audit_service.create_audit_event(
            claim_id=claim_id,
            event_type=AUDIT_EVENT_TYPE_PRE_ASSESSMENT,
            actor=AUDIT_ACTOR_SYSTEM,
            event_description=(
                f"Pre-assessment generated for claim {claim_id} "
                f"with recommendation {RECOMMENDATION_REVIEW_REQUIRED}"
            ),
        )

        return assessment
