from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel
from backend.app.dependencies import get_current_user
from backend.database.repositories.invoice_repo import invoice_repo
from backend.models.user import UserOut
from backend.services.export_service import export_service

router = APIRouter(prefix="/export", tags=["Data Export"])


class BatchExportRequest(BaseModel):
    invoice_ids: List[str]
    format: str = "json"


@router.get("/single/{invoice_id}")
async def export_single_invoice(
    invoice_id: str,
    format: str = Query("json", alias="format"),
    current_user: UserOut = Depends(get_current_user),
):
    content, filename, media_type = await export_service.export_single_invoice(invoice_id, fmt=format)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type=media_type, headers=headers)


@router.post("/batch")
async def export_batch(
    request: BatchExportRequest,
    current_user: UserOut = Depends(get_current_user),
):
    results = []
    for i_id in request.invoice_ids:
        inv = await invoice_repo.get_by_id(i_id)
        if inv:
            results.append({
                "id": inv.id,
                "filename": inv.filename,
                "extracted_data": inv.extracted_data or {},
            })
    return {"count": len(results), "invoices": results}
