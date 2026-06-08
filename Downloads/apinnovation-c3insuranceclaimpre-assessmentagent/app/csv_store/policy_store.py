"""Policy and clause CSV persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from app.constants import POLICY_CLAUSE_COLUMNS
from app.csv_store.base import BaseCSVStore
from app.csv_store.utils import dataframe_row_to_dict


class PolicyStore:
    """Read policy and clause records from CSV files."""

    def __init__(self, data_dir: Path) -> None:
        self._policy_store = BaseCSVStore(
            data_dir / "policies.csv",
            id_column="policy_number",
        )
        self._clause_path = data_dir / "policy_clauses.csv"
        self._policies_cache: pd.DataFrame | None = None
        self._clauses_cache: pd.DataFrame | None = None

    def _load_policies(self) -> pd.DataFrame:
        if self._policies_cache is None:
            self._policies_cache = self._policy_store.read_all()
        return self._policies_cache

    def _load_clauses(self) -> pd.DataFrame:
        if self._clauses_cache is None:
            with self._clause_path.open(encoding="utf-8") as clause_file:
                first_line = clause_file.readline().strip()

            if first_line.lower().startswith("clause_id"):
                self._clauses_cache = pd.read_csv(self._clause_path)
            else:
                self._clauses_cache = pd.read_csv(
                    self._clause_path,
                    header=None,
                    names=POLICY_CLAUSE_COLUMNS,
                )
        return self._clauses_cache

    def get_policy(self, policy_number: str) -> dict[str, Any] | None:
        """Return a single policy by policy_number."""
        return self._policy_store.find_by_id(policy_number)

    def get_policy_clauses(self) -> list[dict[str, Any]]:
        """Return all policy clauses as dictionaries."""
        clauses = self._load_clauses()
        return [dataframe_row_to_dict(row) for _, row in clauses.iterrows()]
