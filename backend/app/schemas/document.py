"""
Insurance Claim Pre-Assurance – Document Pydantic Schemas
Covers document types for all supported domains:
  Health, Life, Motor, Travel, Property, Banking, Disability, Commercial, Liability.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class DocumentType(str, Enum):
    """
    Allowed document types for claim submission, grouped by domain.
    Select the type that best matches the document being uploaded.
    """
    # ── Universal (all domains) ────────────────────────────────────────────────
    CLAIM_FORM            = "claim_form"           # Standard insurer claim form
    IDENTITY_PROOF        = "identity_proof"       # Aadhaar, PAN, Passport
    ADDRESS_PROOF         = "address_proof"        # Utility bill, rent agreement
    POLICY_DOCUMENT       = "policy_document"      # Original policy schedule / bond
    OTHER                 = "other"

    # ── Health ────────────────────────────────────────────────────────────────
    BILL                  = "bill"                 # Hospital / pharmacy bill
    PRESCRIPTION          = "prescription"         # Doctor's prescription
    DISCHARGE_SUMMARY     = "discharge_summary"    # Hospital discharge summary
    LAB_REPORT            = "lab_report"           # Pathology / radiology report
    CONSULTATION_NOTES    = "consultation_notes"   # OPD consultation record
    PRE_AUTH_LETTER       = "pre_auth_letter"      # TPA pre-authorisation

    # ── Life ──────────────────────────────────────────────────────────────────
    DEATH_CERTIFICATE     = "death_certificate"    # Municipal / hospital death certificate
    POST_MORTEM_REPORT    = "post_mortem_report"   # In case of unnatural death
    NOMINEE_ID            = "nominee_id"           # Nominee identity proof
    SUCCESSION_CERTIFICATE = "succession_certificate"  # Legal heir certificate
    EMPLOYER_CERTIFICATE  = "employer_certificate" # Disability / income proof from employer
    DISABILITY_CERTIFICATE = "disability_certificate"  # CMO / medical board certificate

    # ── Motor ─────────────────────────────────────────────────────────────────
    RC_BOOK               = "rc_book"              # Registration Certificate
    DRIVING_LICENCE       = "driving_licence"      # Driver's licence copy
    REPAIR_ESTIMATE       = "repair_estimate"      # Garage / workshop estimate
    SURVEYOR_REPORT       = "surveyor_report"      # Insurance surveyor's inspection report
    FIR_COPY              = "fir_copy"             # Police FIR (for theft / third-party)
    VEHICLE_PHOTOGRAPH    = "vehicle_photograph"   # Photos of damaged vehicle

    # ── Travel ────────────────────────────────────────────────────────────────
    TICKET_COPY           = "ticket_copy"          # Flight / train / bus ticket
    PASSPORT_COPY         = "passport_copy"        # Passport bio page + visa
    CANCELLATION_PROOF    = "cancellation_proof"   # Airline / hotel cancellation letter
    BAGGAGE_IRREGULARITY_REPORT = "baggage_irregularity_report"  # PIR from airline
    MEDICAL_REPORT_ABROAD = "medical_report_abroad"  # Treatment records from abroad
    TRAVEL_INSURANCE_CARD = "travel_insurance_card"  # Emergency assist card

    # ── Property / Home ───────────────────────────────────────────────────────
    FIRE_BRIGADE_REPORT   = "fire_brigade_report"  # Official fire dept report
    VALUATION_REPORT      = "valuation_report"     # Property / asset valuation
    PROPERTY_PHOTOGRAPH   = "property_photograph"  # Photos of damaged property
    MUNICIPAL_REPORT      = "municipal_report"     # Flood / disaster cert from authority
    OWNERSHIP_PROOF       = "ownership_proof"      # Sale deed / title deed

    # ── Banking ───────────────────────────────────────────────────────────────
    BANK_STATEMENT        = "bank_statement"       # Account statement showing dispute
    TRANSACTION_RECEIPT   = "transaction_receipt"  # NEFT / UPI / card transaction slip
    LOAN_AGREEMENT        = "loan_agreement"       # Signed loan sanction letter
    CARD_STATEMENT        = "card_statement"       # Credit / debit card statement
    CHARGEBACK_FORM       = "chargeback_form"      # Bank's dispute / chargeback form

    # ── Commercial / Liability ────────────────────────────────────────────────
    LEGAL_NOTICE          = "legal_notice"         # Third-party legal notice received
    COURT_ORDER           = "court_order"          # Relevant court judgement / order
    BUSINESS_RECORDS      = "business_records"     # P&L, invoices for business loss
    TRADE_LICENCE         = "trade_licence"        # Business / trade licence copy


class OcrStatus(str, Enum):
    """OCR processing state machine values."""
    PENDING    = "PENDING"
    PROCESSING = "PROCESSING"
    DONE       = "DONE"
    FAILED     = "FAILED"


class DocumentResponse(BaseModel):
    """Document record returned in API responses."""
    model_config = {"from_attributes": True}

    id:             str
    claim_id:       str
    document_type:  str
    file_name:      str
    mime_type:      str
    file_size_bytes: Optional[int]
    ocr_status:     str
    ocr_text:       Optional[str]
    uploaded_at:    datetime
