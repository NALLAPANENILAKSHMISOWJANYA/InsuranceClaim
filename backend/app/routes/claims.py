"""
Insurance Claim Pre-Assurance – Claims Router
Handles claim lifecycle: create, read, list, document upload, status update.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.models.claim import Claim
from app.models.document import Document
from app.schemas.claim import ClaimCreate, ClaimResponse, ClaimListResponse, ClaimStatusUpdate
from app.schemas.document import DocumentResponse, DocumentType
from app.services import audit_service
from app.utils.exceptions import ClaimNotFoundError
from app.utils.file_utils import validate_upload, save_upload_file

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Claim CRUD ────────────────────────────────────────────────────────────────

@router.post("/create", response_model=ClaimResponse, status_code=201, summary="Create a new claim")
async def create_claim(
    payload: ClaimCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> ClaimResponse:
    """
    Register a new insurance claim.
    Returns the created claim with a system-generated ID and PENDING status.
    """
    claim_id = f"CLM-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    claim = Claim(
        id=claim_id,
        customer_name=payload.customer_name,
        policy_number=payload.policy_number,
        insurer=payload.insurer.value,
        domain=payload.domain.value,
        policy_type=payload.policy_type.value if payload.policy_type else payload.domain.value,
        claim_sub_type=payload.claim_sub_type.value if payload.claim_sub_type else None,
        claim_amount=payload.claim_amount,
        incident_date=payload.incident_date,
        # Domain-specific optional fields
        diagnosis=payload.diagnosis,
        hospital_name=payload.hospital_name,
        vehicle_number=payload.vehicle_number,
        property_address=payload.property_address,
        account_number=payload.account_number,
        nominee_name=payload.nominee_name,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        status="PENDING",
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)

    audit_service.log_event(
        db=db,
        entity_type="claim",
        entity_id=claim_id,
        action="CREATE",
        new_value={"claim_id": claim_id, "customer": payload.customer_name, "amount": payload.claim_amount},
        ip_address=_get_client_ip(request),
    )

    logger.info("Claim created", extra={"claim_id": claim_id})
    return ClaimResponse.model_validate(claim)


@router.get("", response_model=ClaimListResponse, summary="List all claims")
def list_claims(
    status: Optional[str] = Query(None, description="Filter by claim status"),
    insurer: Optional[str] = Query(None, description="Filter by insurer"),
    domain: Optional[str] = Query(None, description="Filter by domain (health, life, motor, banking…)"),
    claim_sub_type: Optional[str] = Query(None, description="Filter by claim sub-type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ClaimListResponse:
    """
    Return a paginated list of claims.
    Supports optional filtering by status and insurer.
    """
    query = db.query(Claim)
    if status:
        query = query.filter(Claim.status == status.upper())
    if insurer:
        query = query.filter(Claim.insurer == insurer.lower())
    if domain:
        query = query.filter(Claim.domain == domain.lower())
    if claim_sub_type:
        query = query.filter(Claim.claim_sub_type == claim_sub_type.lower())

    total = query.count()
    claims = query.order_by(Claim.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return ClaimListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ClaimResponse.model_validate(c) for c in claims],
    )


@router.get("/{claim_id}", response_model=ClaimResponse, summary="Get claim details")
def get_claim(claim_id: str, db: Session = Depends(get_db)) -> ClaimResponse:
    """Retrieve full details of a single claim by its ID."""
    claim = _get_claim_or_404(claim_id, db)
    return ClaimResponse.model_validate(claim)


@router.patch("/{claim_id}/status", response_model=ClaimResponse, summary="Update claim status (adjuster action)")
def update_claim_status(
    claim_id: str,
    payload: ClaimStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
) -> ClaimResponse:
    """
    Human adjuster action to update the lifecycle status of a claim.
    Writes an audit entry recording the status transition.
    """
    claim = _get_claim_or_404(claim_id, db)
    old_status = claim.status

    claim.status = payload.status.value
    claim.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(claim)

    audit_service.log_event(
        db=db,
        entity_type="claim",
        entity_id=claim_id,
        action="UPDATE",
        actor="adjuster",
        old_value={"status": old_status},
        new_value={"status": payload.status.value, "notes": payload.notes},
        ip_address=_get_client_ip(request),
    )

    logger.info("Claim status updated", extra={"claim_id": claim_id, "old": old_status, "new": payload.status.value})
    return ClaimResponse.model_validate(claim)


# ── Document Upload ───────────────────────────────────────────────────────────

@router.post(
    "/{claim_id}/upload-document",
    response_model=DocumentResponse,
    status_code=201,
    summary="Upload a document to a claim",
)
async def upload_document(
    claim_id: str,
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """
    Upload a supporting document (PDF, JPEG, PNG) to an existing claim.
    Validates MIME type and file size before saving.
    OCR processing is triggered separately via POST /ocr/process/{claim_id}.
    """
    _get_claim_or_404(claim_id, db)
    validate_upload(file)

    saved_path, file_size = await save_upload_file(file, claim_id, document_type.value)

    doc_id = f"DOC-{uuid.uuid4().hex[:10].upper()}"
    document = Document(
        id=doc_id,
        claim_id=claim_id,
        document_type=document_type.value,
        file_name=file.filename or saved_path.name,
        file_path=str(saved_path),
        mime_type=file.content_type,
        file_size_bytes=file_size,
        ocr_status="PENDING",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    audit_service.log_event(
        db=db,
        entity_type="document",
        entity_id=doc_id,
        action="CREATE",
        new_value={"doc_id": doc_id, "claim_id": claim_id, "type": document_type.value, "bytes": file_size},
        ip_address=_get_client_ip(request) if request else None,
    )

    logger.info("Document uploaded", extra={"doc_id": doc_id, "claim_id": claim_id})
    return DocumentResponse.model_validate(document)


@router.get("/{claim_id}/documents", response_model=list[DocumentResponse], summary="List documents for a claim")
def list_documents(claim_id: str, db: Session = Depends(get_db)) -> list[DocumentResponse]:
    """Return all documents attached to a claim."""
    _get_claim_or_404(claim_id, db)
    documents = db.query(Document).filter(Document.claim_id == claim_id).all()
    return [DocumentResponse.model_validate(d) for d in documents]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_claim_or_404(claim_id: str, db: Session) -> Claim:
    """Fetch a claim or raise 404."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise ClaimNotFoundError(claim_id)
    return claim


def _get_client_ip(request: Request) -> str | None:
    """Extract client IP, respecting X-Forwarded-For headers."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else None
