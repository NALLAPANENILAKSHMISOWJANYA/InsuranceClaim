"""CSV store utility helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd


def to_native(value: Any) -> Any:
    """Convert pandas/numpy scalar values to native Python types."""
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def dataframe_row_to_dict(row: pd.Series) -> dict[str, Any]:
    """Convert a single DataFrame row to a JSON-serializable dictionary."""
    return {column: to_native(row[column]) for column in row.index}
