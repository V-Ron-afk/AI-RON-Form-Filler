"""
Async SQLAlchemy database setup.
Uses asyncpg driver for PostgreSQL with connection pooling.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def create_tables():
    """
    Create all tables using IF NOT EXISTS — safe for multiple workers
    and safe to call on every restart regardless of DB state.
    """
    from app.models import user, document, form_submission  # noqa: F401

    async with engine.begin() as conn:
        # Use raw SQL so each statement is atomic and idempotent.
        # Two workers can both run this simultaneously with no conflict.
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id           SERIAL PRIMARY KEY,
                email        VARCHAR(255) NOT NULL UNIQUE,
                hashed_password VARCHAR(255) NOT NULL,
                full_name    VARCHAR(255) NOT NULL,
                is_active    BOOLEAN NOT NULL DEFAULT TRUE,
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS documents (
                id             SERIAL PRIMARY KEY,
                user_id        INTEGER NOT NULL REFERENCES users(id),
                filename       VARCHAR(500) NOT NULL,
                file_path      VARCHAR(1000) NOT NULL,
                file_type      VARCHAR(20) NOT NULL,
                status         VARCHAR(20) NOT NULL DEFAULT 'pending',
                extracted_data JSONB,
                error_message  TEXT,
                created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                processed_at   TIMESTAMPTZ
            )
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS form_submissions (
                id          SERIAL PRIMARY KEY,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                document_id INTEGER NOT NULL REFERENCES documents(id),
                form_data   JSONB NOT NULL,
                label       VARCHAR(255),
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """))

        # Indexes — IF NOT EXISTS prevents duplicate-index errors too
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_users_email ON users(email)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_documents_user_id ON documents(user_id)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_form_submissions_user_id ON form_submissions(user_id)"
        ))


async def get_db():
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session
