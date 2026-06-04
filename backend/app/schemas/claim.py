"""
Insurance Claim Pre-Assurance – Claim Pydantic Schemas
Request/response validation for the /claims endpoints.
Supports all domains: Health, Life, Motor, Travel, Property, Banking, Commercial, Liability, Disability.
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class ClaimStatus(str, Enum):
    """Allowed lifecycle statuses for a claim."""
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    ESCALATED = "ESCALATED"
    CLOSED = "CLOSED"


class DomainType(str, Enum):
    """
    Top-level insurance / financial domain.
    Each domain has its own document requirements, fraud rules, and policy datasets.
    """
    # ── Insurance domains ──────────────────────────────────────────────────────
    HEALTH     = "health"       # Medical hospitalisation, OPD, critical illness
    LIFE       = "life"         # Death claims, maturity, disability, term
    MOTOR      = "motor"        # Own damage, third party, theft
    TRAVEL     = "travel"       # Trip cancellation, baggage loss, medical abroad
    PROPERTY   = "property"     # Home, fire, burglary, flood
    COMMERCIAL = "commercial"   # Business interruption, trade credit, marine
    LIABILITY  = "liability"    # Public/employer/professional liability
    DISABILITY = "disability"   # Personal accident, permanent disability
    GROUP      = "group"        # Corporate group health / life schemes
    # ── Banking / Financial domain ─────────────────────────────────────────────
    BANKING    = "banking"      # Loan insurance, credit card fraud, NEFT disputes
    OTHER      = "other"


class ClaimSubType(str, Enum):
    """
    Sub-classification within a domain.
    Used to drive domain-specific validation and fraud rules.
    """
    # Health
    HOSPITALISATION  = "hospitalisation"
    OPD              = "opd"
    CRITICAL_ILLNESS = "critical_illness"
    MATERNITY        = "maternity"
    DENTAL           = "dental"
    VISION           = "vision"
    # Life
    DEATH            = "death"
    MATURITY         = "maturity"
    SURRENDER        = "surrender"
    RIDER_CLAIM      = "rider_claim"
    # Motor
    OWN_DAMAGE       = "own_damage"
    THIRD_PARTY      = "third_party"
    THEFT            = "theft"
    # Travel
    TRIP_CANCELLATION = "trip_cancellation"
    BAGGAGE_LOSS      = "baggage_loss"
    MEDICAL_ABROAD    = "medical_abroad"
    FLIGHT_DELAY      = "flight_delay"
    # Property
    FIRE              = "fire"
    BURGLARY          = "burglary"
    FLOOD             = "flood"
    EARTHQUAKE        = "earthquake"
    # Banking
    CARD_FRAUD        = "card_fraud"
    NEFT_DISPUTE      = "neft_dispute"
    LOAN_INSURANCE    = "loan_insurance"
    # Disability
    PERMANENT_DISABILITY = "permanent_disability"
    TEMPORARY_DISABILITY = "temporary_disability"
    ACCIDENTAL_DEATH     = "accidental_death"
    # Generic
    OTHER             = "other"


class InsurerType(str, Enum):
    """
    Supported insurer / institution identifiers.
    Maps to sub-folders in datasets/policies/<domain>/<insurer>/.
    """
    # ── Health insurers ────────────────────────────────────────────────────────
    HDFC_ERGO      = "hdfc_ergo"
    STAR_HEALTH    = "star_health"
    ICICI_LOMBARD  = "icici_lombard"
    NIVA_BUPA      = "niva_bupa"
    CARE_HEALTH    = "care_health"
    BAJAJ_ALLIANZ  = "bajaj_allianz"
    NEW_INDIA      = "new_india"
    ORIENTAL       = "oriental"
    UNITED_INDIA   = "united_india"
    TATA_AIG       = "tata_aig"
    RELIANCE_GEN   = "reliance_general"
    # ── Life insurers ──────────────────────────────────────────────────────────
    LIC            = "lic"
    SBI_LIFE       = "sbi_life"
    HDFC_LIFE      = "hdfc_life"
    ICICI_PRU      = "icici_pru"
    MAX_LIFE       = "max_life"
    BAJAJ_LIFE     = "bajaj_allianz_life"
    KOTAK_LIFE     = "kotak_life"
    TATA_AIA       = "tata_aia"
    ADITYA_BIRLA   = "aditya_birla_life"
    # ── Banking institutions ───────────────────────────────────────────────────
    SBI            = "sbi"
    HDFC_BANK      = "hdfc_bank"
    ICICI_BANK     = "icici_bank"
    AXIS_BANK      = "axis_bank"
    PNB            = "pnb"
    CANARA_BANK    = "canara_bank"
    # ── Catch-all ─────────────────────────────────────────────────────────────
    OTHER          = "other"


# ── Request Bodies ────────────────────────────────────────────────────────────

class ClaimCreate(BaseModel):
    """Payload to create a new claim record. Works for any domain."""
    customer_name:  str       = Field(..., min_length=2, max_length=100, examples=["Ravi Kumar"])
    policy_number:  str       = Field(..., min_length=5, max_length=100, examples=["HDFC-HLT-2024-001234"])
    insurer:        InsurerType
    domain:         DomainType  = Field(..., description="Top-level insurance/financial domain")
    policy_type:    DomainType  = Field(
        None,
        description="Alias for domain (kept for backward compatibility). If omitted, domain is used.",
        examples=["health"],
    )
    claim_sub_type: Optional[ClaimSubType] = Field(
        None,
        description="Sub-classification within the domain (e.g. 'hospitalisation' under 'health')",
    )
    claim_amount:   float     = Field(..., gt=0, examples=[85000.0])
    incident_date:  date
    # Domain-flexible optional fields
    diagnosis:      Optional[str] = Field(None, max_length=500, description="Health/Life: diagnosis or cause of death")
    hospital_name:  Optional[str] = Field(None, max_length=200, description="Health: treating hospital")
    vehicle_number: Optional[str] = Field(None, max_length=20,  description="Motor: vehicle registration number")
    property_address: Optional[str] = Field(None, max_length=500, description="Property: address of insured property")
    account_number: Optional[str] = Field(None, max_length=50,  description="Banking: bank account / card number (masked)")
    nominee_name:   Optional[str] = Field(None, max_length=100, description="Life: nominee name")
    contact_email:  Optional[EmailStr] = None
    contact_phone:  Optional[str] = Field(None, max_length=15,  description="Claimant contact phone number")

    def model_post_init(self, __context) -> None:
        """If policy_type not set, mirror domain for backward compatibility."""
        if self.policy_type is None:
            self.policy_type = self.domain


class ClaimStatusUpdate(BaseModel):
    """Payload for a human adjuster to update claim status."""
    status: ClaimStatus
    notes:  Optional[str] = Field(None, max_length=1000)


# ── Response Bodies ───────────────────────────────────────────────────────────

class ClaimResponse(BaseModel):
    """Full claim record returned in API responses."""
    model_config = {"from_attributes": True}

    id:               str
    customer_name:    str
    policy_number:    str
    insurer:          str
    domain:           Optional[str]
    policy_type:      str
    claim_sub_type:   Optional[str]
    claim_amount:     float
    incident_date:    date
    diagnosis:        Optional[str]
    hospital_name:    Optional[str]
    vehicle_number:   Optional[str]
    property_address: Optional[str]
    account_number:   Optional[str]
    nominee_name:     Optional[str]
    contact_email:    Optional[str]
    contact_phone:    Optional[str]
    status:           str
    created_at:       datetime
    updated_at:       datetime


class ClaimListResponse(BaseModel):
    """Paginated list of claims."""
    total:     int
    page:      int
    page_size: int
    items:     list[ClaimResponse]
