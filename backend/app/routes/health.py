"""
Insurance Claim Pre-Assurance – Health Check Endpoint
GET /health
Returns application version, database connectivity status, and server time.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.dependencies import get_db

router = APIRouter()


@router.get("/health", summary="Health check", tags=["Health"])
def health_check(db: Session = Depends(get_db)) -> dict:
    """
    Returns the current health of the API.

    - **status**: "healthy" | "degraded"
    - **database**: "connected" | "disconnected"
    - **version**: application version string
    - **timestamp**: current UTC time (ISO-8601)
    """
    db_status = _check_database(db)
    overall_status = "healthy" if db_status == "connected" else "degraded"

    return {
        "status": overall_status,
        "version": settings.VERSION,
        "app_name": settings.APP_NAME,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _check_database(db: Session) -> str:
    """Ping the database with a lightweight query."""
    try:
        db.execute(text("SELECT 1"))
        return "connected"
    except Exception:
        return "disconnected"
