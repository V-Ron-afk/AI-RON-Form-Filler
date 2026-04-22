"""
Document routes
================
POST /api/documents/upload    — upload file, trigger AI extraction
GET  /api/documents/          — list user's documents
GET  /api/documents/{id}      — get single document
GET  /api/documents/{id}/extraction — get structured extraction result
"""

import os
import uuid
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.db import crud
from app.models.user import User
from app.schemas.schemas import DocumentOut, ExtractionResult
from app.services.ai.google_docai_service import google_docai_service
from app.services.form.mapping_service import map_fields_to_form, get_confidence_map, FORM_SCHEMA

router = APIRouter()

UPLOAD_DIR = Path("/tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _validate_file(file: UploadFile) -> str:
    """Check extension and size; return extension."""
    ext = Path(file.filename or "").suffix.lstrip(".").lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )
    return ext


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a document and immediately run AI extraction.
    The heavy work happens synchronously here; for very large scale
    move extraction to a background task / Celery queue.
    """
    ext = _validate_file(file)

    # Read file bytes (enforce size limit)
    file_bytes = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB} MB limit")

    # Save to disk with a UUID name to avoid collisions
    safe_name = f"{uuid.uuid4()}.{ext}"
    dest = UPLOAD_DIR / safe_name
    dest.write_bytes(file_bytes)

    # Create DB record
    doc = await crud.create_document(
        db,
        user_id=current_user.id,
        filename=file.filename or safe_name,
        file_path=str(dest),
        file_type=ext,
    )

    # Run AI extraction
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    try:
        await crud.update_document_extraction(db, doc.id, {}, "processing")
        extraction = await google_docai_service.analyze_document(str(dest), file_bytes, content_type)
        extraction.document_id = doc.id

        # Persist structured extraction
        stored = {
            "fields": [f.model_dump() for f in extraction.fields],
            "tables": extraction.tables,
            "raw_text": extraction.raw_text,
            "model_used": extraction.model_used,
        }
        doc = await crud.update_document_extraction(db, doc.id, stored, "completed")
        doc.processed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(doc)

    except Exception as e:
        await crud.update_document_extraction(db, doc.id, {}, "failed")
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {str(e)}")

    return DocumentOut.model_validate(doc)


@router.get("/", response_model=list[DocumentOut])
async def list_documents(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return paginated list of user's uploaded documents."""
    docs = await crud.list_documents(db, current_user.id, skip=skip, limit=limit)
    return [DocumentOut.model_validate(d) for d in docs]


@router.get("/{doc_id}", response_model=DocumentOut)
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    doc = await crud.get_document(db, doc_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut.model_validate(doc)


@router.get("/{doc_id}/extraction")
async def get_extraction(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return extraction result enriched with:
    - mapped form values (canonical field → value)
    - per-field confidence scores (for UI colour-coding)
    - form schema (field definitions for the dynamic form)
    """
    doc = await crud.get_document(db, doc_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "completed" or not doc.extracted_data:
        raise HTTPException(status_code=422, detail=f"Document status is '{doc.status}'")

    raw = doc.extracted_data
    from app.schemas.schemas import ExtractedField
    fields = [ExtractedField(**f) for f in raw.get("fields", [])]

    form_values = map_fields_to_form(fields)
    confidence_map = get_confidence_map(fields)

    return {
        "document_id": doc.id,
        "status": doc.status,
        "model_used": raw.get("model_used"),
        "raw_text_preview": (raw.get("raw_text") or "")[:500],
        "fields": raw.get("fields", []),
        "tables": raw.get("tables", []),
        "form_values": form_values,
        "confidence_map": confidence_map,
        "form_schema": [f.model_dump() for f in FORM_SCHEMA],
    }
