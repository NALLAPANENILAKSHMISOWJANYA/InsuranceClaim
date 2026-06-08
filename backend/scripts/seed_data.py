"""
Insurance Claim Pre-Assurance – Dev Seed Script
Inserts sample claims and documents for local development & testing.
Run: python scripts/seed_data.py
"""
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, engine, Base  # noqa: E402
from app.models.claim import Claim  # noqa: E402
from app.models import document, assessment, audit_log  # noqa: E402, F401

Base.metadata.create_all(bind=engine)

SAMPLE_CLAIMS = [
    {
        "id": "CLM-20260602-SEED01",
        "customer_name": "Ravi Kumar",
        "policy_number": "HDFC-HLT-2024-001234",
        "insurer": "hdfc_ergo",
        "policy_type": "health",
        "claim_amount": 85000.0,
        "incident_date": date(2026, 5, 20),
        "diagnosis": "Appendicitis",
        "hospital_name": "Apollo Hospital Chennai",
        "contact_email": "ravi@example.com",
        "status": "PENDING",
    },
    {
        "id": "CLM-20260602-SEED02",
        "customer_name": "Priya Singh",
        "policy_number": "STAR-HLT-2023-005678",
        "insurer": "star_health",
        "policy_type": "health",
        "claim_amount": 210000.0,
        "incident_date": date(2026, 5, 15),
        "diagnosis": "Diabetes Type 2 - Complications",
        "hospital_name": "Fortis Hospital Delhi",
        "contact_email": "priya@example.com",
        "status": "UNDER_REVIEW",
    },
    {
        "id": "CLM-20260602-SEED03",
        "customer_name": "Arjun Mehta",
        "policy_number": "ICICI-MTR-2025-009900",
        "insurer": "icici_lombard",
        "policy_type": "motor",
        "claim_amount": 55000.0,
        "incident_date": date(2026, 5, 28),
        "diagnosis": None,
        "hospital_name": None,
        "contact_email": "arjun@example.com",
        "status": "PENDING",
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        inserted = 0
        for data in SAMPLE_CLAIMS:
            exists = db.query(Claim).filter(Claim.id == data["id"]).first()
            if not exists:
                db.add(Claim(**data))
                inserted += 1
        db.commit()
        print(f"Seed complete. {inserted} new claims inserted.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
