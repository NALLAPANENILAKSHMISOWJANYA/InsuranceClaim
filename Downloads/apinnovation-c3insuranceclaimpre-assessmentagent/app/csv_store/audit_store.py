"""Audit event CSV persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from app.constants import AUDIT_EVENT_COLUMNS
from app.csv_store.base import BaseCSVStore
from app.csv_store.utils import dataframe_row_to_dict


class AuditStore:
    """Append-only audit event storage."""

    def __init__(self, data_dir: Path) -> None:
        self._store = BaseCSVStore(data_dir / "audit_events.csv")
        self._file_path = data_dir / "audit_events.csv"

    def _read_events(self) -> pd.DataFrame:
        if not self._file_path.exists() or self._file_path.stat().st_size == 0:
            return pd.DataFrame(columns=AUDIT_EVENT_COLUMNS)
        events = self._store.read_all()
        if events.empty:
            return pd.DataFrame(columns=AUDIT_EVENT_COLUMNS)
        return events

    @staticmethod
    def _next_event_id(audit_events: pd.DataFrame) -> str:
        """Generate the next sequential audit event identifier."""
        if audit_events.empty:
            return "AUD-001"
        numeric_ids = []
        for event_id in audit_events["event_id"].astype(str):
            if event_id.startswith("AUD-"):
                suffix = event_id.replace("AUD-", "", 1)
                if suffix.isdigit():
                    numeric_ids.append(int(suffix))
        next_number = max(numeric_ids, default=0) + 1
        return f"AUD-{next_number:03d}"

    def get_events(self) -> list[dict[str, Any]]:
        """Return all audit events."""
        events = self._read_events()
        return [dataframe_row_to_dict(row) for _, row in events.iterrows()]

    def append_event(
        self,
        claim_id: str,
        event_type: str,
        actor: str,
        event_description: str,
    ) -> dict[str, Any]:
        """Append a new audit event without modifying prior records."""
        audit_events = self._read_events()
        event = {
            "event_id": self._next_event_id(audit_events),
            "claim_id": claim_id,
            "event_type": event_type,
            "actor": actor,
            "event_description": event_description,
            "event_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        updated_events = pd.concat(
            [audit_events, pd.DataFrame([event])],
            ignore_index=True,
        )
        self._store.save_all(updated_events)
        return event
