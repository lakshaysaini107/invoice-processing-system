from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from backend.core.security import get_current_user
from backend.core.logging import logger
from backend.app.dependencies import get_processing_service, get_invoice_repository

if TYPE_CHECKING:
    from backend.database.repositories.invoice_repo import InvoiceRepository
    from backend.services.processing_service import ProcessingService

router = APIRouter(prefix="/process", tags=["processing"])

# ==================== Schemas ====================

class ProcessRequest(BaseModel):
    invoice_id: str
    use_cache: bool = True
    prefer_handwriting_ocr: bool = False

class ProcessResponse(BaseModel):
    invoice_id: str
    status: str
    message: str
    processing_started_at: datetime

class ProcessStatusResponse(BaseModel):
    invoice_id: str
    status: str
    progress: int
    current_step: str
    extracted_data: Optional[dict] = None
    confidence_scores: Optional[dict] = None
    error_message: Optional[str] = None

# ==================== Endpoints ====================

@router.post("/start", response_model=ProcessResponse)
async def start_processing(
    request: ProcessRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    processing_service: ProcessingService = Depends(get_processing_service),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """
    Trigger invoice processing pipeline
    Process: Upload → Preprocessing → OCR → Layout Detection → Vision LLM → NER → Validation
    """
    # Verify invoice exists and belongs to user
    invoice = await invoice_repo.get_by_id(request.invoice_id)

    if not invoice or invoice["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if invoice.get("processing_status") == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invoice is already being processed"
        )
    
    # Update status to processing
    await invoice_repo.update(
        request.invoice_id,
        {"processing_status": "processing", "started_at": datetime.utcnow()},
        return_updated=False,
    )
    
    # Start background processing
    background_tasks.add_task(
        processing_service.process_invoice,
        invoice_id=request.invoice_id,
        file_path=invoice["file_path"],
        use_cache=request.use_cache,
        prefer_handwriting_ocr=request.prefer_handwriting_ocr,
    )
    
    logger.info(f"Processing started for invoice {request.invoice_id}")
    
    return ProcessResponse(
        invoice_id=request.invoice_id,
        status="processing",
        message="Invoice processing started",
        processing_started_at=datetime.utcnow()
    )

@router.get("/status/{invoice_id}", response_model=ProcessStatusResponse)
async def get_processing_status(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """Get real-time processing status of an invoice"""
    invoice = await invoice_repo.get_by_id(invoice_id)

    if not invoice or invoice["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    return ProcessStatusResponse(
        invoice_id=invoice_id,
        status=invoice.get("processing_status", "pending"),
        progress=invoice.get("progress", 0),
        current_step=invoice.get("current_step") or "initialization",
        extracted_data=invoice.get("extracted_data"),
        confidence_scores=invoice.get("confidence_scores"),
        error_message=invoice.get("error_message")
    )

@router.post("/retry/{invoice_id}")
async def retry_processing(
    invoice_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    processing_service: ProcessingService = Depends(get_processing_service),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """Retry processing for a failed invoice"""
    invoice = await invoice_repo.get_by_id(invoice_id)

    if not invoice or invoice["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Reset processing status
    await invoice_repo.update(
        invoice_id,
        {
            "processing_status": "processing",
            "error_message": None,
            "progress": 0
        },
        return_updated=False,
    )
    
    # Start processing again
    background_tasks.add_task(
        processing_service.process_invoice,
        invoice_id=invoice_id,
        file_path=invoice["file_path"],
        use_cache=False
    )
    
    logger.info(f"Processing retried for invoice {invoice_id}")
    
    return {"message": "Processing retry started"}
