"""Audit business workflows."""

from __future__ import annotations

from typing import Any

from app.csv_store.audit_store import AuditStore


class AuditService:
    """Coordinates audit event persistence and retrieval."""

    def __init__(self, audit_store: AuditStore) -> None:
        self._audit_store = audit_store

    def create_audit_event(
        self,
        claim_id: str,
        event_type: str,
        actor: str,
        event_description: str,
    ) -> dict[str, Any]:
        """Write a new audit event."""
        return self._audit_store.append_event(
            claim_id=claim_id,
            event_type=event_type,
            actor=actor,
            event_description=event_description,
        )

    def get_audit_history(self) -> list[dict[str, Any]]:
        """Retrieve all audit events."""
        return self._audit_store.get_events()
