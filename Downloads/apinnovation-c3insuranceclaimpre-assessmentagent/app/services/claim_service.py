"""Claim business workflows."""

from __future__ import annotations

from typing import Any

from app.csv_store.claim_store import ClaimStore


class ClaimService:
    """Provides claim retrieval and dashboard statistics."""

    def __init__(self, claim_store: ClaimStore) -> None:
        self._claim_store = claim_store

    def get_all_claims(self) -> list[dict[str, Any]]:
        """Return all claims."""
        return self._claim_store.get_claims()

    def get_claim_by_id(self, claim_id: str) -> dict[str, Any] | None:
        """Return a single claim by identifier."""
        return self._claim_store.get_claim(claim_id)

    def get_dashboard_stats(self) -> dict[str, int]:
        """Return claim counts aggregated by insurance type."""
        claims = self._claim_store.get_claims()
        insurance_types = [claim["insurance_type"] for claim in claims]
        return {
            "total_claims": len(claims),
            "health_claims": insurance_types.count("HEALTH"),
            "vehicle_claims": insurance_types.count("VEHICLE"),
            "life_claims": insurance_types.count("LIFE"),
            "home_claims": insurance_types.count("HOME"),
            "crop_claims": insurance_types.count("CROP"),
        }
