"""
Insurance Claim Pre-Assurance – Application Configuration
All environment variables and path constants are defined here.
No hardcoded secrets or magic numbers anywhere else.
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Insurance Claim Pre-Assurance"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite:///./claimsense.db"

    # ── File Storage ──────────────────────────────────────────────────────────
    UPLOAD_DIR: Path = Path("uploads")
    VECTOR_STORE_DIR: Path = Path("vector_store")
    POLICY_DATASET_DIR: Path = Path("datasets/policies")
    LOG_DIR: Path = Path("logs")

    # ── Upload Constraints ────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_MIME_TYPES: list = ["application/pdf", "image/jpeg", "image/png"]

    # ── RAG / Embeddings ──────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 5
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    # ── LLM (external API only – no local deployment) ─────────────────────────
    LLM_PROVIDER: str = "anthropic"          # "anthropic" | "huggingface" | "deepseek"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "claude-3-haiku-20240307"

    # ── Fraud Rules ───────────────────────────────────────────────────────────
    # High-value thresholds are domain-specific (amounts in INR)
    FRAUD_HIGH_VALUE_THRESHOLD: float = 500_000.0    # Default / health ₹5L
    FRAUD_HIGH_VALUE_THRESHOLD_HEALTH: float = 500_000.0   # ₹5 lakh
    FRAUD_HIGH_VALUE_THRESHOLD_LIFE: float = 5_000_000.0   # ₹50 lakh
    FRAUD_HIGH_VALUE_THRESHOLD_MOTOR: float = 1_000_000.0  # ₹10 lakh
    FRAUD_HIGH_VALUE_THRESHOLD_TRAVEL: float = 200_000.0   # ₹2 lakh
    FRAUD_HIGH_VALUE_THRESHOLD_PROPERTY: float = 2_000_000.0  # ₹20 lakh
    FRAUD_HIGH_VALUE_THRESHOLD_BANKING: float = 200_000.0  # ₹2 lakh
    FRAUD_HIGH_VALUE_THRESHOLD_DISABILITY: float = 1_000_000.0  # ₹10 lakh
    FRAUD_RAPID_RECLAIM_DAYS: int = 90
    FRAUD_MIN_DOCUMENTS: int = 2

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure runtime directories exist
for _dir in (settings.UPLOAD_DIR, settings.VECTOR_STORE_DIR, settings.LOG_DIR):
    _dir.mkdir(parents=True, exist_ok=True)
