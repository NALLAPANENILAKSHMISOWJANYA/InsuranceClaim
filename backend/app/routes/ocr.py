"""
Insurance Claim Pre-Assurance – OCR Router (Sprint 2)
Triggers text extraction on uploaded documents and returns results.
"""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.document import Document
from app.services import ocr_service
from app.utils.exceptions import ClaimNotFoundError, DocumentNotFoundError
from app.models.claim import Claim

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/process/{claim_id}",
    summary="Trigger OCR for all PENDING documents on a claim",
)
def process_ocr(claim_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Iterates every document attached to the claim whose `ocr_status` is PENDING,
    extracts text with pdfplumber / Tesseract, and persists the result.

    Returns a summary of how many documents were processed and their outcomes.
    """
    # Validate claim exists
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise ClaimNotFoundError(claim_id)

    pending_docs = (
        db.query(Document)
        .filter(Document.claim_id == claim_id, Document.ocr_status == "PENDING")
        .all()
    )

    if not pending_docs:
        return {
            "claim_id": claim_id,
            "processed": 0,
            "message": "No PENDING documents found for this claim.",
        }

    results = []
    for doc in pending_docs:
        # Mark as in-progress
        doc.ocr_status = "PROCESSING"
        db.commit()

        extracted_text = ocr_service.extract_text(doc.file_path, doc.mime_type)

        if extracted_text:
            doc.ocr_text = extracted_text
            doc.ocr_status = "DONE"
        else:
            doc.ocr_status = "FAILED"

        db.commit()
        db.refresh(doc)

        results.append({
            "document_id": doc.id,
            "file_name": doc.file_name,
            "ocr_status": doc.ocr_status,
            "char_count": len(extracted_text) if extracted_text else 0,
        })
        logger.info(
            "OCR completed",
            extra={"doc_id": doc.id, "status": doc.ocr_status, "chars": len(extracted_text or "")},
        )

    done_count = sum(1 for r in results if r["ocr_status"] == "DONE")
    failed_count = sum(1 for r in results if r["ocr_status"] == "FAILED")

    return {
        "claim_id": claim_id,
        "processed": len(results),
        "done": done_count,
        "failed": failed_count,
        "documents": results,
    }


@router.get(
    "/result/{document_id}",
    summary="Get OCR extracted text for a specific document",
)
def get_ocr_result(document_id: str, db: Session = Depends(get_db)) -> dict:
    """
    Returns the OCR status and extracted text for a single document.
    Useful for inspecting individual extraction results before triggering assessment.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise DocumentNotFoundError(document_id)

    return {
        "document_id": doc.id,
        "claim_id": doc.claim_id,
        "file_name": doc.file_name,
        "ocr_status": doc.ocr_status,
        "char_count": len(doc.ocr_text) if doc.ocr_text else 0,
        "ocr_text": doc.ocr_text,
    }
