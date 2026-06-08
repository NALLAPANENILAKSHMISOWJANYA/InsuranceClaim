"""Application startup utilities."""

from pathlib import Path

from app.constants import REQUIRED_DATASETS


def validate_datasets(data_dir: Path) -> None:
    """Ensure all required CSV datasets exist before application startup."""
    for filename in REQUIRED_DATASETS:
        dataset_path = data_dir / filename
        if not dataset_path.exists():
            raise RuntimeError(f"Missing required dataset: {filename}")
