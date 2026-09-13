from typing import Dict, Optional
from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel
from backend.app.dependencies import get_current_user
from backend.core.exceptions import NotFoundException
from backend.database.repositories.invoice_repo import invoice_repo
from backend.models.inoice import InvoiceOut, ProcessingStatus
from backend.models.user import UserOut
from backend.services.processing_service import processing_service

router = APIRouter(prefix="/process", tags=["Processing Pipeline"])


class ProcessStartRequest(BaseModel):
    invoice_id: str


@router.post("/start")
async def start_processing(
    request: ProcessStartRequest,
    background_tasks: BackgroundTasks,
    current_user: UserOut = Depends(get_current_user),
):
    invoice = await invoice_repo.get_by_id(request.invoice_id)
    if not invoice:
        raise NotFoundException(f"Invoice {request.invoice_id} not found.")

    background_tasks.add_task(processing_service.process_invoice, request.invoice_id)

    return {
        "status": "processing",
        "message": f"Processing started for invoice {request.invoice_id}",
        "invoice_id": request.invoice_id,
    }


@router.get("/status/{invoice_id}")
async def get_processing_status(
    invoice_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    invoice = await invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found.")

    return {
        "invoice_id": invoice.id,
        "processing_status": invoice.processing_status,
        "overall_confidence": invoice.overall_confidence,
        "error_message": invoice.error_message,
        "current_step": "completed" if invoice.processing_status == ProcessingStatus.COMPLETED.value else invoice.processing_status,
    }


@router.post("/retry/{invoice_id}")
async def retry_processing(
    invoice_id: str,
    background_tasks: BackgroundTasks,
    current_user: UserOut = Depends(get_current_user),
):
    invoice = await invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found.")

    background_tasks.add_task(processing_service.process_invoice, invoice_id)
    return {
        "status": "processing",
        "message": f"Retry started for invoice {invoice_id}",
        "invoice_id": invoice_id,
    }
