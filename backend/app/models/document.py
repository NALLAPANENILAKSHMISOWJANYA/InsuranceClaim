"""
Insurance Claim Pre-Assurance – Document ORM Model
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from app.core.database import Base


class Document(Base):
    """A supporting document attached to a claim (PDF, image, etc.)."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    claim_id = Column(
        String, ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    document_type = Column(String(50), nullable=False)
    # Allowed: claim_form | bill | prescription | discharge_summary | other
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)

    # OCR state machine: PENDING → PROCESSING → DONE | FAILED
    ocr_status = Column(String(20), nullable=False, default="PENDING")
    ocr_text = Column(Text, nullable=True)   # raw extracted text blob

    uploaded_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} type={self.document_type} ocr={self.ocr_status}>"
