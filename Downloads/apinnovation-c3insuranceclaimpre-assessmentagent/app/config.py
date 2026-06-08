"""Application configuration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """ClaimSense AI runtime settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="ClaimSense AI", alias="APP_NAME")
    version: str = Field(default="1.0.0", alias="VERSION")
    data_dir: Path = Field(
        default=PROJECT_ROOT / "data",
        validation_alias=AliasChoices("DATA_DIR", "CLAIMSENSE_DATA_DIR"),
    )
    rag_top_k: int = Field(default=10, alias="RAG_TOP_K")
    low_rag_similarity: float = Field(default=0.0, alias="LOW_RAG_SIMILARITY")

    @property
    def APP_NAME(self) -> str:
        return self.app_name

    @property
    def VERSION(self) -> str:
        return self.version

    @property
    def DATA_DIR(self) -> Path:
        return self.data_dir

    @property
    def RAG_TOP_K(self) -> int:
        return self.rag_top_k

    @property
    def LOW_RAG_SIMILARITY(self) -> float:
        return self.low_rag_similarity


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


def get_settings_for_data_dir(data_dir: Path | None = None) -> Settings:
    """Return settings, optionally overriding the data directory."""
    if data_dir is None:
        return get_settings()
    return get_settings().model_copy(update={"data_dir": data_dir})
