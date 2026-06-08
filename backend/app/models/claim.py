"""
Insurance Claim Pre-Assurance – Claim ORM Model
"""
from datetime import date, datetime, timezone
from sqlalchemy import Column, String, Float, Date, DateTime, Text
from app.core.database import Base


class Claim(Base):
    """Represents an insurance claim submitted for pre-assessment."""

    __tablename__ = "claims"

    id = Column(String, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    policy_number = Column(String(100), nullable=False, index=True)
    insurer = Column(String(50), nullable=False, index=True)

    # Domain-aware fields
    domain = Column(String(50), nullable=True, index=True)          # health | life | motor | travel | property | banking | …
    policy_type = Column(String(50), nullable=False)                # mirrors domain for backward compat
    claim_sub_type = Column(String(50), nullable=True, index=True)  # hospitalisation | death | own_damage | …

    claim_amount = Column(Float, nullable=False)
    incident_date = Column(Date, nullable=False)

    # Health-specific
    diagnosis = Column(Text, nullable=True)
    hospital_name = Column(String(200), nullable=True)

    # Motor-specific
    vehicle_number = Column(String(20), nullable=True)

    # Property-specific
    property_address = Column(Text, nullable=True)

    # Banking-specific
    account_number = Column(String(50), nullable=True)

    # Life-specific
    nominee_name = Column(String(100), nullable=True)

    # Contact
    contact_email = Column(String(150), nullable=True)
    contact_phone = Column(String(15), nullable=True)

    # Lifecycle status – only humans may set final status
    status = Column(String(30), nullable=False, default="PENDING", index=True)

    created_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Claim id={self.id} status={self.status}>"