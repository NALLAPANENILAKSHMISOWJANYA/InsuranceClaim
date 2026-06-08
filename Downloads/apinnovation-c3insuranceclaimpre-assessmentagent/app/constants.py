"""Shared application constants."""

POLICY_CLAUSE_COLUMNS = [
    "clause_id",
    "insurance_type",
    "clause_type",
    "clause_name",
    "clause_text",
]

AUDIT_EVENT_COLUMNS = [
    "event_id",
    "claim_id",
    "event_type",
    "actor",
    "event_description",
    "event_timestamp",
]

REQUIRED_DATASETS = [
    "claims.csv",
    "policies.csv",
    "policy_clauses.csv",
    "audit_events.csv",
]

RECOMMENDATION_REVIEW_REQUIRED = "REVIEW_REQUIRED"
GENERATED_BY = "ClaimSense AI"
AUDIT_EVENT_TYPE_PRE_ASSESSMENT = "PRE_ASSESSMENT"
AUDIT_ACTOR_SYSTEM = "SYSTEM"

OPENAPI_TAGS = [
    {"name": "System", "description": "Application health and status endpoints."},
    {"name": "Claims", "description": "Insurance claim lookup endpoints."},
    {"name": "Policies", "description": "Policy lookup endpoints."},
    {"name": "RAG", "description": "Keyword-based policy clause retrieval."},
    {"name": "Assessment", "description": "AI-assisted pre-assessment endpoints."},
    {"name": "Dashboard", "description": "Operational dashboard statistics."},
]
