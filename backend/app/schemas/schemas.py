"""
Pydantic v2 schemas — the "contract" between API and clients.
Separates ORM models from API shapes (never expose hashed_password, etc.)
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ─────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── Extraction ────────────────────────────────────────────────────────────────

class ExtractedField(BaseModel):
    """A single key-value pair extracted from the document."""
    key: str
    value: Optional[str]
    confidence: float          # 0.0 – 1.0
    page: Optional[int] = None


class ExtractionResult(BaseModel):
    """Full extraction payload returned to the frontend."""
    document_id: int
    status: str
    fields: List[ExtractedField]
    tables: List[List[Dict[str, Any]]] = []  # list of tables, each a list of row-dicts
    raw_text: Optional[str] = None
    model_used: str


# ── Documents ─────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: int
    filename: str
    file_type: str
    status: str
    extracted_data: Optional[Dict[str, Any]]
    created_at: datetime
    processed_at: Optional[datetime]

    model_config = {"from_attributes": True}


# ── Forms ─────────────────────────────────────────────────────────────────────

class FormFieldDef(BaseModel):
    """Definition of a single form field (from the form template)."""
    name: str            # machine-readable key
    label: str           # display label
    field_type: str      # "text" | "date" | "number" | "email" | "select"
    required: bool = False
    options: Optional[List[str]] = None   # for "select" type


class FormSubmitRequest(BaseModel):
    document_id: int
    form_data: Dict[str, Any]   # field_name -> value
    label: Optional[str] = None


class FormSubmissionOut(BaseModel):
    id: int
    document_id: int
    form_data: Dict[str, Any]
    label: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Export ────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    submission_id: int
    format: str   # "json" | "pdf"
