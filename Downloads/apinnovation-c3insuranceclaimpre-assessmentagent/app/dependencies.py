"""FastAPI dependency injection and service wiring."""

from __future__ import annotations

from fastapi import FastAPI, Request

from app.config import Settings
from app.csv_store import AuditStore, ClaimStore, PolicyStore
from app.services import (
    AssessmentService,
    AuditService,
    ClaimService,
    PolicyService,
)


def wire_services(application: FastAPI, settings: Settings) -> None:
    """Initialize stores, services, and attach them to application state."""
    claim_store = ClaimStore(settings.data_dir)
    policy_store = PolicyStore(settings.data_dir)
    audit_store = AuditStore(settings.data_dir)

    claim_service = ClaimService(claim_store)
    policy_service = PolicyService(policy_store)
    audit_service = AuditService(audit_store)
    assessment_service = AssessmentService(
        claim_service=claim_service,
        policy_service=policy_service,
        audit_service=audit_service,
    )

    application.state.claim_service = claim_service
    application.state.policy_service = policy_service
    application.state.audit_service = audit_service
    application.state.assessment_service = assessment_service


def get_claim_service(request: Request) -> ClaimService:
    """Return the claim service from application state."""
    return request.app.state.claim_service


def get_policy_service(request: Request) -> PolicyService:
    """Return the policy service from application state."""
    return request.app.state.policy_service


def get_assessment_service(request: Request) -> AssessmentService:
    """Return the assessment service from application state."""
    return request.app.state.assessment_service
