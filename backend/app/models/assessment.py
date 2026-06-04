"""
Insurance Claim Pre-Assurance – Assessment ORM Model
Stores the pre-assessment result for a claim.
Human adjuster can set override verdict and notes.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, ForeignKey
from app.core.database import Base


class Assessment(Base):
    """
    Pre-assessment report produced by the assessment engine.
    Verdict is advisory only – a human adjuster always makes the final call.
    """

    __tablename__ = "assessments"

    id = Column(String, primary_key=True, index=True)
    claim_id = Column(
        String, ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )

    # ── Engine verdict ────────────────────────────────────────────────────────
    # APPROVE | REJECT | ESCALATE | PENDING_REVIEW
    verdict = Column(String(30), nullable=False)
    confidence_score = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)

    # ── Policy checks ─────────────────────────────────────────────────────────
    coverage_eligible = Column(Boolean, nullable=True)
    waiting_period_cleared = Column(Boolean, nullable=True)
    ped_conflict = Column(Boolean, nullable=True)
    room_rent_within_limit = Column(Boolean, nullable=True)

    # ── Signals (stored as JSON text) ─────────────────────────────────────────
    fraud_signals = Column(Text, nullable=True)        # JSON array
    missing_documents = Column(Text, nullable=True)    # JSON array
    policy_chunks_used = Column(Text, nullable=True)   # JSON array of RAG chunks

    # ── Human-in-the-loop override ────────────────────────────────────────────
    adjuster_override = Column(String(30), nullable=True)   # NULL until human acts
    adjuster_notes = Column(Text, nullable=True)
    adjuster_reviewed_at = Column(DateTime, nullable=True)

    assessed_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Assessment claim={self.claim_id} verdict={self.verdict}>"
