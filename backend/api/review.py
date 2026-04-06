from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.core.security import get_current_user
from backend.services.review_service import ReviewService
from backend.database.repositories.invoice_repo import InvoiceRepository
from backend.core.logging import logger
from backend.app.dependencies import get_review_service, get_invoice_repository

router = APIRouter(prefix="/review", tags=["review"])

# ==================== Schemas ====================

class FieldCorrection(BaseModel):
    field_name: str
    original_value: Any
    corrected_value: Any
    confidence: Optional[float] = None

class ReviewSubmission(BaseModel):
    invoice_id: str
    corrections: List[FieldCorrection]
    notes: Optional[str] = None
    approved: bool

class ReviewResponse(BaseModel):
    invoice_id: str
    status: str
    reviewed_by: str
    reviewed_at: datetime
    corrections_count: int

class InvoiceDetailsResponse(BaseModel):
    invoice_id: str
    filename: str
    extracted_data: dict
    confidence_scores: dict
    processing_status: str
    review_status: Optional[str] = None
    ready_for_review: bool = False
    progress: int = 0
    current_step: Optional[str] = None
    error_message: Optional[str] = None

# ==================== Endpoints ====================

@router.get("/{invoice_id}/details", response_model=InvoiceDetailsResponse)
async def get_invoice_details(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """Get invoice details for manual review"""
    invoice = await invoice_repo.get_by_id(invoice_id)

    if not invoice or invoice["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    processing_status = str(invoice.get("processing_status") or "pending")
    ready_for_review = processing_status in {"completed", "reviewed"}

    return InvoiceDetailsResponse(
        invoice_id=invoice_id,
        filename=invoice["filename"],
        extracted_data=invoice.get("extracted_data") or {},
        confidence_scores=invoice.get("confidence_scores") or {},
        processing_status=processing_status,
        review_status=invoice.get("review_status"),
        ready_for_review=ready_for_review,
        progress=int(invoice.get("progress") or 0),
        current_step=invoice.get("current_step"),
        error_message=invoice.get("error_message"),
    )

@router.post("/{invoice_id}/submit", response_model=ReviewResponse)
async def submit_review(
    invoice_id: str,
    submission: ReviewSubmission,
    current_user: dict = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """Submit corrections and approve/reject invoice"""
    invoice = await invoice_repo.get_by_id(invoice_id)

    if not invoice or invoice["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Apply corrections
    updated_data = await review_service.apply_corrections(
        extracted_data=invoice.get("extracted_data", {}),
        corrections=submission.corrections
    )
    
    # Update invoice
    review_status = "approved" if submission.approved else "rejected"
    
    update_data = {
        "extracted_data": updated_data,
        "review_status": review_status,
        "reviewed_by": current_user["_id"],
        "reviewed_at": datetime.utcnow(),
        "corrections": [c.dict() for c in submission.corrections],
        "review_notes": submission.notes,
        "processing_status": "reviewed"
    }
    
    await invoice_repo.update(invoice_id, update_data, return_updated=False)
    
    logger.info(
        f"Invoice {invoice_id} reviewed by {current_user['email']} - Status: {review_status}"
    )
    
    return ReviewResponse(
        invoice_id=invoice_id,
        status=review_status,
        reviewed_by=current_user["email"],
        reviewed_at=datetime.utcnow(),
        corrections_count=len(submission.corrections)
    )

@router.get("/{invoice_id}/comparison")
async def get_correction_comparison(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """Get side-by-side comparison of original vs corrected data"""
    invoice = await invoice_repo.get_by_id(invoice_id)

    if not invoice or invoice["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return {
        "invoice_id": invoice_id,
        "original_extraction": invoice.get("extracted_data", {}),
        "corrections_applied": invoice.get("corrections", []),
        "final_data": invoice.get("extracted_data", {}),
        "confidence_scores": invoice.get("confidence_scores", {})
    }
