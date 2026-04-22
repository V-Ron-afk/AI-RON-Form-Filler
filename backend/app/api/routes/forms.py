"""Form submission routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.db import crud
from app.models.user import User
from app.schemas.schemas import FormSubmitRequest, FormSubmissionOut

router = APIRouter()


@router.post("/submit", response_model=FormSubmissionOut, status_code=201)
async def submit_form(
    payload: FormSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save the user-edited form data to the database."""
    doc = await crud.get_document(db, payload.document_id, current_user.id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    sub = await crud.create_submission(
        db,
        user_id=current_user.id,
        document_id=payload.document_id,
        form_data=payload.form_data,
    )
    if payload.label:
        sub.label = payload.label
        await db.commit()
        await db.refresh(sub)

    return FormSubmissionOut.model_validate(sub)


@router.get("/", response_model=list[FormSubmissionOut])
async def list_submissions(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subs = await crud.list_submissions(db, current_user.id, skip=skip, limit=limit)
    return [FormSubmissionOut.model_validate(s) for s in subs]


@router.get("/{sub_id}", response_model=FormSubmissionOut)
async def get_submission(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = await crud.get_submission(db, sub_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    return FormSubmissionOut.model_validate(sub)
