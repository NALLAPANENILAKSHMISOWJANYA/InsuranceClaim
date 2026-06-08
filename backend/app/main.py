"""
Insurance Claim Pre-Assurance – FastAPI Application Entry Point
Registers all routers, middleware, and startup hooks.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.database import engine, Base

from app.routes import health, claims, ocr, rag, assessment, fraud, analytics

# ── Boot ──────────────────────────────────────────────────────────────────────
setup_logging()

# Auto-create tables on startup (Alembic manages migrations in staging/prod)
Base.metadata.create_all(bind=engine)

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description=(
        "Backend API for **Insurance Claim Pre-Assurance** – an Insurance Claim Pre-Assessment Agent. "
        "Human-in-the-loop is mandatory. No automatic claim approval or rejection."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Middleware ─────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["Health"])
app.include_router(claims.router, prefix="/claims", tags=["Claims"])
app.include_router(ocr.router, prefix="/ocr", tags=["OCR"])
app.include_router(rag.router, prefix="/rag", tags=["RAG"])
app.include_router(assessment.router, prefix="/assessment", tags=["Assessment"])
app.include_router(fraud.router, prefix="/fraud", tags=["Fraud"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])