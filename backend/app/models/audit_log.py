"""
Insurance Claim Pre-Assurance – AuditLog ORM Model
Immutable append-only log. No UPDATE or DELETE ever touches this table.
Supports full traceability for every state change in the system.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.core.database import Base


class AuditLog(Base):
    """
    Append-only audit trail.
    Every mutation on claims, documents, or assessments writes one row here.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # What was changed
    entity_type = Column(String(30), nullable=False)   # "claim" | "document" | "assessment"
    entity_id = Column(String(100), nullable=False, index=True)

    # What happened
    action = Column(String(50), nullable=False)
    # CREATE | UPDATE | DELETE | OCR_RUN | OCR_COMPLETE | ASSESSMENT_RUN | ADJUSTER_OVERRIDE

    # Who did it
    actor = Column(String(50), nullable=False, default="system")
    # "system" for automated steps, "adjuster" for human actions

    # State snapshots (JSON text for flexibility)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    # Request context
    ip_address = Column(String(45), nullable=True)   # supports IPv6

    timestamp = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog entity={self.entity_type}:{self.entity_id} "
            f"action={self.action} actor={self.actor}>"
        )
