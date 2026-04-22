"""
Central configuration — reads from environment variables / .env file.
All secrets live here; never hard-code credentials in source files.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────────
    APP_NAME: str = "AI Form Filler"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/formfiller"

    # ── Google Document AI ─────────────────────────────────────────────────
    # Path to your service-account JSON key file (mounted into Docker at runtime)
    # Leave blank to use MOCK mode — no GCP account needed for local dev.
    GOOGLE_APPLICATION_CREDENTIALS: str = ""   # leave blank to use ADC (gcloud login)

    # Your GCP project number (NOT project ID string)
    # Found at: console.cloud.google.com → select project → Project info card
    GOOGLE_CLOUD_PROJECT_ID: str = ""

    # Cloud region where your Document AI processor lives
    GOOGLE_CLOUD_LOCATION: str = "us"   # or "eu"

    # Processor ID from: console.cloud.google.com/ai/document-ai/processors
    # Free-tier processor type: "FORM_PARSER_PROCESSOR"
    GOOGLE_DOCUMENTAI_PROCESSOR_ID: str = ""

    # ── CORS ───────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:4200",   # Angular dev server
        "http://localhost:80",
        "http://frontend:80",
    ]

    # ── File uploads ───────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "jpg", "jpeg", "png", "tiff", "bmp", "gif", "webp"]

    # ── Export ─────────────────────────────────────────────────────────────
    EXPORT_DIR: str = "/tmp/exports"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
