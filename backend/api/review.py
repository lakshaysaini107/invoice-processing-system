from typing import Any, Dict
from fastapi import APIRouter, Depends
from backend.app.dependencies import get_current_user
from backend.core.exceptions import NotFoundException
from backend.database.repositories.invoice_repo import invoice_repo
from backend.models.inoice import InvoiceOut, InvoiceReviewSubmit
from backend.models.user import UserOut
from backend.services.review_service import review_service

router = APIRouter(prefix="/review", tags=["Human Review"])


@router.get("/{invoice_id}/details")
async def get_review_details(
    invoice_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    invoice = await invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found.")

    return {
        "invoice_id": invoice.id,
        "filename": invoice.filename,
        "processing_status": invoice.processing_status,
        "review_status": invoice.review_status,
        "overall_confidence": invoice.overall_confidence,
        "extracted_data": invoice.extracted_data or {},
        "confidence_scores": invoice.confidence_scores or {},
        "ocr_result": invoice.ocr_result or {},
        "layout_info": invoice.layout_info or {},
        "entities": invoice.entities or {},
        "corrections": invoice.corrections or [],
        "review_notes": invoice.review_notes,
    }


@router.post("/{invoice_id}/submit", response_model=InvoiceOut)
async def submit_review(
    invoice_id: str,
    payload: InvoiceReviewSubmit,
    current_user: UserOut = Depends(get_current_user),
):
    return await review_service.submit_review(
        invoice_id=invoice_id,
        updated_extracted_data=payload.extracted_data,
        review_status=payload.review_status or "approved",
        review_notes=payload.review_notes,
        reviewed_by=current_user.username,
    )
