"""
Insurance Claim Pre-Assurance – Audit Service
Append-only writes to the audit_logs table.
All mutations in the system must call one of these functions.
"""
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


def log_event(
    db: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    actor: str = "system",
    old_value: dict | None = None,
    new_value: dict | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """
    Write a single audit entry to the database.
    This is the ONLY function that creates AuditLog rows.

    Args:
        db:          Active database session.
        entity_type: Type of entity changed: "claim" | "document" | "assessment".
        entity_id:   Primary key of the changed entity.
        action:      What happened: "CREATE" | "UPDATE" | "OCR_RUN" | etc.
        actor:       Who triggered the action: "system" | "adjuster".
        old_value:   Dict snapshot of state before the change (optional).
        new_value:   Dict snapshot of state after the change (optional).
        ip_address:  Originating IP address (optional).

    Returns:
        The persisted AuditLog instance.
    """
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        actor=actor,
        old_value=json.dumps(old_value, default=str) if old_value else None,
        new_value=json.dumps(new_value, default=str) if new_value else None,
        ip_address=ip_address,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    logger.info(
        "Audit event recorded",
        extra={
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "actor": actor,
        },
    )
    return entry
