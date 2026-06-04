"""
Insurance Claim Pre-Assurance – FastAPI Dependency Providers
Centralises shared dependencies so routes stay thin.
"""
from collections.abc import Generator
from sqlalchemy.orm import Session
from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session and ensure it is closed after the request,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
