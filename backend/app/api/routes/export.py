"""Export routes — download submission as JSON or PDF."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.database import get_db
from app.db import crud
from app.models.user import User
from app.services.export.export_service import export_json, export_pdf

router = APIRouter()


@router.get("/{sub_id}/json")
async def download_json(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download form submission as JSON."""
    sub = await crud.get_submission(db, sub_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    data = export_json(sub.form_data, sub.id)
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="submission_{sub_id}.json"'},
    )


@router.get("/{sub_id}/pdf")
async def download_pdf(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download form submission as PDF."""
    sub = await crud.get_submission(db, sub_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    data = export_pdf(sub.form_data, sub.id)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="submission_{sub_id}.pdf"'},
    )
