"""Base CSV persistence layer."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import pandas as pd

from app.csv_store.utils import dataframe_row_to_dict, to_native


class BaseCSVStore:
    """Thread-safe CSV read/write operations backed by pandas."""

    def __init__(self, file_path: Path, id_column: str | None = None) -> None:
        self.file_path = file_path
        self.id_column = id_column
        self._lock = threading.Lock()

    def read_all(self) -> pd.DataFrame:
        """Read all records from the CSV file."""
        with self._lock:
            if not self.file_path.exists() or self.file_path.stat().st_size == 0:
                return pd.DataFrame()
            return pd.read_csv(self.file_path)

    def save_all(self, dataframe: pd.DataFrame) -> None:
        """Persist the full dataframe to the CSV file."""
        with self._lock:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            dataframe.to_csv(self.file_path, index=False)

    def find_by_id(self, record_id: str) -> dict[str, Any] | None:
        """Find a single record by its identifier column."""
        if self.id_column is None:
            raise ValueError("id_column must be configured to use find_by_id")

        dataframe = self.read_all()
        if dataframe.empty or self.id_column not in dataframe.columns:
            return None

        matched = dataframe[dataframe[self.id_column] == record_id]
        if matched.empty:
            return None
        return dataframe_row_to_dict(matched.iloc[0])

    def create(self, record: dict[str, Any]) -> dict[str, Any]:
        """Append a new record to the CSV file."""
        with self._lock:
            dataframe = self.read_all()
            new_record = {key: to_native(value) for key, value in record.items()}
            updated = pd.concat(
                [dataframe, pd.DataFrame([new_record])],
                ignore_index=True,
            )
            self.save_all(updated)
            return new_record

    def update(self, record_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        """Update an existing record by identifier."""
        if self.id_column is None:
            raise ValueError("id_column must be configured to use update")

        with self._lock:
            dataframe = self.read_all()
            if dataframe.empty or self.id_column not in dataframe.columns:
                return None

            matched_index = dataframe.index[dataframe[self.id_column] == record_id]
            if len(matched_index) == 0:
                return None

            row_index = matched_index[0]
            for key, value in updates.items():
                dataframe.at[row_index, key] = to_native(value)

            self.save_all(dataframe)
            return dataframe_row_to_dict(dataframe.loc[row_index])
