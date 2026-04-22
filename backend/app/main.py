"""
AI Auto Form Filler - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.database import create_tables
from app.api.routes import auth, documents, forms, export

logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Starting AI Form Filler API...")
    await create_tables()
    logger.info("Database tables ready.")
    yield
    logger.info("Shutting down AI Form Filler API.")


app = FastAPI(
    title="AI Auto Form Filler API",
    description="""
    Automatically extract structured data from documents (PDF, images)
    using **Google Document AI** and auto-fill web forms.

    ## Features
    - 📄 Document upload (PDF, JPG, PNG, TIFF, WebP)
    - 🤖 AI-powered field extraction via Google Document AI (Form Parser)
    - 🆓 Free tier: 1,000 pages/month — no credit card required
    - 📋 Dynamic form auto-filling with confidence scores
    - ✏️ User-editable results before submission
    - 💾 PostgreSQL persistence
    - 📦 JSON / PDF export
    - 🔐 JWT authentication
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── Middleware ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Routers ─────────────────────────────────────────────────────────────────

app.include_router(auth.router,      prefix="/api/auth",      tags=["Authentication"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(forms.router,     prefix="/api/forms",     tags=["Forms"])
app.include_router(export.router,    prefix="/api/export",    tags=["Export"])


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
