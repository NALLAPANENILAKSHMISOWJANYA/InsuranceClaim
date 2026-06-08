"""Claim CSV persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.csv_store.base import BaseCSVStore
from app.csv_store.utils import dataframe_row_to_dict


class ClaimStore:
    """Read and write claim records from claims.csv."""

    def __init__(self, data_dir: Path) -> None:
        self._store = BaseCSVStore(data_dir / "claims.csv", id_column="claim_id")
        self._cache: pd.DataFrame | None = None

    def _load_claims(self) -> pd.DataFrame:
        if self._cache is None:
            self._cache = self._store.read_all()
        return self._cache

    def get_claims(self) -> list[dict[str, Any]]:
        """Return all claims as dictionaries."""
        claims = self._load_claims()
        return [dataframe_row_to_dict(row) for _, row in claims.iterrows()]

    def get_claim(self, claim_id: str) -> dict[str, Any] | None:
        """Return a single claim by claim_id."""
        return self._store.find_by_id(claim_id)

    def save_claim(self, claim: dict[str, Any]) -> dict[str, Any]:
        """Persist a claim record."""
        existing = self.get_claim(str(claim["claim_id"]))
        if existing is None:
            saved = self._store.create(claim)
        else:
            saved = self._store.update(str(claim["claim_id"]), claim)
        self._cache = None
        return saved or claim
