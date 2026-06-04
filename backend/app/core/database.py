"""
Insurance Claim Pre-Assurance – Database Engine & Session Factory
Uses SQLAlchemy 2.x with a single SQLite file for sandbox.
Switch DATABASE_URL in .env to postgresql+psycopg2://... for production.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings

# connect_args is required only for SQLite (single-thread safety)
_connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass
