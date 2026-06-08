"""
Insurance Claim Pre-Assurance – Fraud Detection Service (Sprint 3)

Runs a battery of rule-based signal checks against a claim.
Results are advisory ONLY – a human adjuster always makes the final call.

Rules implemented
─────────────────
Signal code                   │ Description
──────────────────────────────┼──────────────────────────────────────────────────────
HIGH_VALUE                    │ Claim exceeds domain-specific high-value threshold
RAPID_RECLAIM                 │ Previous claim by same policy found within N days
INSUFFICIENT_DOCS             │ Fewer than FRAUD_MIN_DOCUMENTS uploaded
MISSING_DISCHARGE_SUMMARY     │ No discharge_summary (health only)
MISSING_DEATH_CERTIFICATE     │ No death_certificate (life only)
MISSING_DRIVING_LICENCE       │ No driving_licence (motor only)
MISSING_BANK_STATEMENT        │ No bank_statement (banking only)
MISSING_CLAIM_FORM            │ No claim_form uploaded
OCR_FAILED_DOCS               │ One or more documents failed OCR
WEEKEND_ADMISSION             │ Incident date falls on Saturday or Sunday
ROUND_AMOUNT                  │ Claim amount suspiciously round (% 10,000 == 0)
DUPLICATE_POLICY_ACTIVE       │ More than one PENDING claim on same policy

Each rule returns a FraudSignal dataclass.
The public API is check(claim_id, db) → FraudResult.
"""
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.claim import Claim
from app.models.document import Document

logger = logging.getLogger(__name__)


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class FraudSignal:
    code: str           # e.g. "HIGH_VALUE"
    severity: str       # "LOW" | "MEDIUM" | "HIGH"
    description: str    # human-readable explanation
    detail: dict = field(default_factory=dict)   # any extra data


@dataclass
class FraudResult:
    claim_id: str
    signals: list[FraudSignal]
    risk_level: str          # "CLEAR" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    risk_score: int          # 0-100  (weighted sum of signal severities)
    summary: str             # one-line human readable verdict

    # Severity → weight mapping (used for risk_score)
    _WEIGHTS: dict = field(default_factory=lambda: {"LOW": 10, "MEDIUM": 25, "HIGH": 40})

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "summary": self.summary,
            "signal_count": len(self.signals),
            "signals": [
                {
                    "code": s.code,
                    "severity": s.severity,
                    "description": s.description,
                    "detail": s.detail,
                }
                for s in self.signals
            ],
        }


# ── Public API ────────────────────────────────────────────────────────────────

def check(claim_id: str, db: Session) -> FraudResult:
    """
    Run all fraud rules against the given claim and return a FraudResult.

    Does NOT write to the database – the assessment engine is responsible
    for persisting signals into assessments.fraud_signals (JSON).

    Raises ValueError if the claim is not found.
    """
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise ValueError(f"Claim '{claim_id}' not found.")

    documents = db.query(Document).filter(Document.claim_id == claim_id).all()

    # Previous claims for the same policy number (excluding this one)
    prior_claims = (
        db.query(Claim)
        .filter(Claim.policy_number == claim.policy_number, Claim.id != claim_id)
        .all()
    )

    # All PENDING claims for the same policy number
    open_claims = (
        db.query(Claim)
        .filter(
            Claim.policy_number == claim.policy_number,
            Claim.id != claim_id,
            Claim.status == "PENDING",
        )
        .all()
    )

    signals: list[FraudSignal] = []

    # Run every rule
    signals += _rule_high_value(claim)
    signals += _rule_rapid_reclaim(claim, prior_claims)
    signals += _rule_insufficient_docs(claim, documents)
    signals += _rule_missing_discharge_summary(claim, documents)
    signals += _rule_missing_death_certificate(claim, documents)
    signals += _rule_missing_driving_licence(claim, documents)
    signals += _rule_missing_bank_statement(claim, documents)
    signals += _rule_missing_claim_form(claim, documents)
    signals += _rule_ocr_failed_docs(claim, documents)
    signals += _rule_weekend_admission(claim)
    signals += _rule_round_amount(claim)
    signals += _rule_duplicate_policy_active(claim, open_claims)

    result = _build_result(claim_id, signals)
    logger.info(
        "Fraud check complete",
        extra={
            "claim_id": claim_id,
            "risk_level": result.risk_level,
            "risk_score": result.risk_score,
            "signal_count": len(signals),
        },
    )
    return result


# ── Rules ─────────────────────────────────────────────────────────────────────

def _rule_high_value(claim: Claim) -> list[FraudSignal]:
    """Use a domain-specific threshold so life/property claims aren't over-flagged."""
    domain = (claim.domain or claim.policy_type or "other").lower()
    threshold_map = {
        "health":     settings.FRAUD_HIGH_VALUE_THRESHOLD_HEALTH,
        "life":       settings.FRAUD_HIGH_VALUE_THRESHOLD_LIFE,
        "motor":      settings.FRAUD_HIGH_VALUE_THRESHOLD_MOTOR,
        "travel":     settings.FRAUD_HIGH_VALUE_THRESHOLD_TRAVEL,
        "property":   settings.FRAUD_HIGH_VALUE_THRESHOLD_PROPERTY,
        "banking":    settings.FRAUD_HIGH_VALUE_THRESHOLD_BANKING,
        "disability": settings.FRAUD_HIGH_VALUE_THRESHOLD_DISABILITY,
    }
    threshold = threshold_map.get(domain, settings.FRAUD_HIGH_VALUE_THRESHOLD)
    if claim.claim_amount > threshold:
        return [FraudSignal(
            code="HIGH_VALUE",
            severity="HIGH",
            description=(
                f"Claim amount ₹{claim.claim_amount:,.0f} exceeds the {domain} domain "
                f"high-value threshold of ₹{threshold:,.0f}."
            ),
            detail={"claim_amount": claim.claim_amount, "threshold": threshold, "domain": domain},
        )]
    return []


def _rule_rapid_reclaim(claim: Claim, prior_claims: list[Claim]) -> list[FraudSignal]:
    window_days = settings.FRAUD_RAPID_RECLAIM_DAYS
    cutoff: date = claim.incident_date - timedelta(days=window_days)
    recent = [c for c in prior_claims if c.incident_date and c.incident_date >= cutoff]
    if recent:
        return [FraudSignal(
            code="RAPID_RECLAIM",
            severity="HIGH",
            description=(
                f"Policy {claim.policy_number} has {len(recent)} prior claim(s) "
                f"with incident date within the last {window_days} days."
            ),
            detail={
                "window_days": window_days,
                "prior_claim_ids": [c.id for c in recent],
                "prior_incident_dates": [str(c.incident_date) for c in recent],
            },
        )]
    return []


def _rule_insufficient_docs(claim: Claim, documents: list[Document]) -> list[FraudSignal]:
    min_docs = settings.FRAUD_MIN_DOCUMENTS
    if len(documents) < min_docs:
        return [FraudSignal(
            code="INSUFFICIENT_DOCS",
            severity="MEDIUM",
            description=(
                f"Only {len(documents)} document(s) uploaded; "
                f"minimum required is {min_docs}."
            ),
            detail={"uploaded": len(documents), "required": min_docs},
        )]
    return []


def _rule_missing_discharge_summary(claim: Claim, documents: list[Document]) -> list[FraudSignal]:
    # Only relevant for health claims
    domain = (claim.domain or claim.policy_type or "").lower()
    if domain != "health":
        return []
    has_discharge = any(d.document_type == "discharge_summary" for d in documents)
    if not has_discharge:
        return [FraudSignal(
            code="MISSING_DISCHARGE_SUMMARY",
            severity="MEDIUM",
            description="No discharge summary uploaded for this health claim.",
            detail={"domain": domain},
        )]
    return []


def _rule_missing_death_certificate(claim: Claim, documents: list[Document]) -> list[FraudSignal]:
    """Life death claims must have a death certificate."""
    domain = (claim.domain or claim.policy_type or "").lower()
    sub_type = (claim.claim_sub_type or "").lower()
    if domain != "life" or sub_type not in ("death", "accidental_death", ""):
        return []
    has_cert = any(d.document_type == "death_certificate" for d in documents)
    if not has_cert:
        return [FraudSignal(
            code="MISSING_DEATH_CERTIFICATE",
            severity="HIGH",
            description="No death certificate uploaded for this life insurance death claim.",
            detail={"domain": domain, "claim_sub_type": sub_type},
        )]
    return []


def _rule_missing_driving_licence(claim: Claim, documents: list[Document]) -> list[FraudSignal]:
    """Motor claims must include the driver's licence."""
    domain = (claim.domain or claim.policy_type or "").lower()
    if domain != "motor":
        return []
    has_licence = any(d.document_type == "driving_licence" for d in documents)
    if not has_licence:
        return [FraudSignal(
            code="MISSING_DRIVING_LICENCE",
            severity="MEDIUM",
            description="No driving licence uploaded for this motor claim.",
            detail={"domain": domain},
        )]
    return []


def _rule_missing_bank_statement(claim: Claim, documents: list[Document]) -> list[FraudSignal]:
    """Banking claims must have a bank statement or transaction record."""
    domain = (claim.domain or claim.policy_type or "").lower()
    if domain != "banking":
        return []
    has_statement = any(
        d.document_type in ("bank_statement", "transaction_receipt", "card_statement")
        for d in documents
    )
    if not has_statement:
        return [FraudSignal(
            code="MISSING_BANK_STATEMENT",
            severity="HIGH",
            description="No bank statement or transaction record uploaded for this banking claim.",
            detail={"domain": domain},
        )]
    return []


def _rule_missing_claim_form(claim: Claim, documents: list[Document]) -> list[FraudSignal]:
    has_form = any(d.document_type == "claim_form" for d in documents)
    if not has_form:
        return [FraudSignal(
            code="MISSING_CLAIM_FORM",
            severity="LOW",
            description="No claim form document uploaded.",
            detail={},
        )]
    return []


def _rule_ocr_failed_docs(claim: Claim, documents: list[Document]) -> list[FraudSignal]:
    failed = [d for d in documents if d.ocr_status == "FAILED"]
    if failed:
        return [FraudSignal(
            code="OCR_FAILED_DOCS",
            severity="MEDIUM",
            description=(
                f"{len(failed)} document(s) could not be read by OCR and may be "
                f"unreadable, corrupted, or intentionally obscured."
            ),
            detail={"failed_document_ids": [d.id for d in failed]},
        )]
    return []


def _rule_weekend_admission(claim: Claim) -> list[FraudSignal]:
    # weekday(): Mon=0 … Sun=6
    if claim.incident_date and claim.incident_date.weekday() >= 5:
        day_name = "Saturday" if claim.incident_date.weekday() == 5 else "Sunday"
        return [FraudSignal(
            code="WEEKEND_ADMISSION",
            severity="LOW",
            description=(
                f"Incident date {claim.incident_date} falls on a {day_name}. "
                "Weekend admissions are flagged for additional verification."
            ),
            detail={"incident_date": str(claim.incident_date), "day": day_name},
        )]
    return []


def _rule_round_amount(claim: Claim) -> list[FraudSignal]:
    amount = claim.claim_amount
    # Flag amounts that are exact multiples of 10,000 and above 50,000
    if amount >= 50_000 and amount % 10_000 == 0:
        return [FraudSignal(
            code="ROUND_AMOUNT",
            severity="LOW",
            description=(
                f"Claim amount ₹{amount:,.0f} is a suspiciously round number "
                "(exact multiple of ₹10,000)."
            ),
            detail={"claim_amount": amount},
        )]
    return []


def _rule_duplicate_policy_active(claim: Claim, open_claims: list[Claim]) -> list[FraudSignal]:
    if open_claims:
        return [FraudSignal(
            code="DUPLICATE_POLICY_ACTIVE",
            severity="HIGH",
            description=(
                f"Policy {claim.policy_number} has {len(open_claims)} other "
                f"PENDING claim(s) currently open."
            ),
            detail={"open_claim_ids": [c.id for c in open_claims]},
        )]
    return []


# ── Result builder ────────────────────────────────────────────────────────────

_SEVERITY_WEIGHT = {"LOW": 10, "MEDIUM": 25, "HIGH": 40}


def _build_result(claim_id: str, signals: list[FraudSignal]) -> FraudResult:
    """Compute a weighted risk score and derive a risk level from the signals."""
    raw_score = sum(_SEVERITY_WEIGHT.get(s.severity, 0) for s in signals)
    # Cap at 100
    risk_score = min(raw_score, 100)

    if risk_score == 0:
        risk_level = "CLEAR"
        summary = "No fraud signals detected. Claim appears routine."
    elif risk_score <= 15:
        risk_level = "LOW"
        summary = "Minor signals detected. Proceed with standard review."
    elif risk_score <= 40:
        risk_level = "MEDIUM"
        summary = "Moderate signals detected. Enhanced verification recommended."
    elif risk_score <= 70:
        risk_level = "HIGH"
        summary = "High-risk signals present. Escalate to senior adjuster."
    else:
        risk_level = "CRITICAL"
        summary = "Critical fraud risk. Hold claim and initiate investigation."

    return FraudResult(
        claim_id=claim_id,
        signals=signals,
        risk_level=risk_level,
        risk_score=risk_score,
        summary=summary,
    )
