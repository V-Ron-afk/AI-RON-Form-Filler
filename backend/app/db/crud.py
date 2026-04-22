"""
CRUD helper functions — thin wrappers around SQLAlchemy queries.
Keeps route handlers clean and testable.
"""

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.document import Document
from app.models.form_submission import FormSubmission
from app.core.security import hash_password


# ── Users ────────────────────────────────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, email: str, password: str, full_name: str) -> User:
    user = User(email=email, hashed_password=hash_password(password), full_name=full_name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ── Documents ────────────────────────────────────────────────────────────────

async def create_document(
    db: AsyncSession, user_id: int, filename: str, file_path: str, file_type: str
) -> Document:
    doc = Document(
        user_id=user_id, filename=filename, file_path=file_path, file_type=file_type
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def get_document(db: AsyncSession, doc_id: int, user_id: int) -> Optional[Document]:
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_document_extraction(
    db: AsyncSession, doc_id: int, extracted_data: dict, status: str
) -> Optional[Document]:
    doc = await db.get(Document, doc_id)
    if doc:
        doc.extracted_data = extracted_data
        doc.status = status
        await db.commit()
        await db.refresh(doc)
    return doc


async def list_documents(db: AsyncSession, user_id: int, skip=0, limit=20) -> List[Document]:
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


# ── Form Submissions ──────────────────────────────────────────────────────────

async def create_submission(
    db: AsyncSession, user_id: int, document_id: int, form_data: dict
) -> FormSubmission:
    sub = FormSubmission(user_id=user_id, document_id=document_id, form_data=form_data)
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def get_submission(db: AsyncSession, sub_id: int, user_id: int) -> Optional[FormSubmission]:
    result = await db.execute(
        select(FormSubmission).where(
            FormSubmission.id == sub_id, FormSubmission.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def list_submissions(
    db: AsyncSession, user_id: int, skip=0, limit=20
) -> List[FormSubmission]:
    result = await db.execute(
        select(FormSubmission)
        .where(FormSubmission.user_id == user_id)
        .order_by(FormSubmission.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())
