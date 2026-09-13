from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile
from backend.app.dependencies import get_current_user
from backend.core.exceptions import NotFoundException
from backend.database.repositories.invoice_repo import invoice_repo
from backend.models.inoice import InvoiceOut
from backend.models.user import UserOut
from backend.services.upload_service import upload_service

router = APIRouter(prefix="/invoices", tags=["Upload & Invoice Management"])


@router.post("/upload", response_model=InvoiceOut)
async def upload_invoice(
    file: UploadFile = File(...),
    current_user: UserOut = Depends(get_current_user),
):
    return await upload_service.save_uploaded_file(file, user_id=current_user.id)


@router.get("/list", response_model=List[InvoiceOut])
async def list_invoices(
    current_user: UserOut = Depends(get_current_user),
):
    return await invoice_repo.list_all()


@router.get("/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    invoice_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    invoice = await invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found.")
    return invoice


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    invoice = await invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found.")
    await invoice_repo.delete(invoice_id)
    return {"message": "Invoice deleted successfully", "invoice_id": invoice_id}
