"""
Insurance Claim Pre-Assurance – Pytest Configuration & Shared Fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.dependencies import get_db
from app.main import app

# ── In-memory SQLite for tests ────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_claimsense.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """
    Provides a TestClient with a fresh in-memory database for each test.
    Tables are created before the test and dropped after.
    """
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """Provides a raw DB session for direct model manipulation in tests."""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)


# ── Shared test data ──────────────────────────────────────────────────────────
SAMPLE_CLAIM_PAYLOAD = {
    "customer_name": "Test User",
    "policy_number": "TEST-HLT-2024-000001",
    "insurer": "hdfc_ergo",
    "domain": "health",
    "policy_type": "health",
    "claim_sub_type": "hospitalisation",
    "claim_amount": 50000.0,
    "incident_date": "2026-05-01",
    "diagnosis": "Fever",
    "hospital_name": "Test Hospital",
    "contact_email": "test@example.com",
}

SAMPLE_LIFE_CLAIM_PAYLOAD = {
    "customer_name": "Priya Sharma",
    "policy_number": "LIC-TERM-2023-000042",
    "insurer": "lic",
    "domain": "life",
    "claim_sub_type": "death",
    "claim_amount": 1_000_000.0,
    "incident_date": "2026-04-10",
    "nominee_name": "Anjali Sharma",
    "contact_email": "anjali.sharma@example.com",
}

SAMPLE_MOTOR_CLAIM_PAYLOAD = {
    "customer_name": "Arjun Mehta",
    "policy_number": "HDFC-MOT-2025-000099",
    "insurer": "hdfc_ergo",
    "domain": "motor",
    "claim_sub_type": "own_damage",
    "claim_amount": 75_000.0,
    "incident_date": "2026-05-20",
    "vehicle_number": "MH-12-AB-1234",
    "contact_email": "arjun.mehta@example.com",
}

SAMPLE_BANKING_CLAIM_PAYLOAD = {
    "customer_name": "Sneha Patel",
    "policy_number": "HDFC-BANK-CARD-000555",
    "insurer": "hdfc_bank",
    "domain": "banking",
    "claim_sub_type": "card_fraud",
    "claim_amount": 45_000.0,
    "incident_date": "2026-05-28",
    "account_number": "XXXX-XXXX-XXXX-1234",
    "contact_email": "sneha.patel@example.com",
}
