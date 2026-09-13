from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from backend.app.dependencies import get_current_user
from backend.core.exceptions import NotFoundException
from backend.database.repositories.erp_invoice_repo import erp_invoice_repo
from backend.database.repositories.invoice_repo import invoice_repo
from backend.models.inoice import ERPInvoiceSave
from backend.models.user import UserOut

router = APIRouter(prefix="/erp", tags=["ERP Handoff & Integration"])

# In-memory storage for current handoff invoice ID
CURRENT_HANDOFF_INVOICE_ID: Optional[str] = None


class SetCurrentInvoiceRequest(BaseModel):
    invoice_id: str


def _format_erp_payload(invoice_id: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
    bank = extracted_data.get("bank_details") or {}
    return {
        "source_invoice_id": invoice_id,
        "invoice_number": str(extracted_data.get("invoice_number") or ""),
        "invoice_date": str(extracted_data.get("invoice_date") or ""),
        "due_date": str(extracted_data.get("due_date") or ""),
        "vendor_name": str(extracted_data.get("vendor_name") or ""),
        "vendor_gst": str(extracted_data.get("vendor_gst") or ""),
        "vendor_address": str(extracted_data.get("vendor_address") or ""),
        "buyer_name": str(extracted_data.get("buyer_name") or ""),
        "buyer_gst": str(extracted_data.get("buyer_gst") or ""),
        "buyer_address": str(extracted_data.get("buyer_address") or ""),
        "invoice_amount": str(extracted_data.get("invoice_amount") if extracted_data.get("invoice_amount") is not None else ""),
        "tax_amount": str(extracted_data.get("tax_amount") if extracted_data.get("tax_amount") is not None else ""),
        "total_amount": str(extracted_data.get("total_amount") if extracted_data.get("total_amount") is not None else ""),
        "tax_rate": str(extracted_data.get("tax_rate") if extracted_data.get("tax_rate") is not None else ""),
        "currency": str(extracted_data.get("currency") or "INR"),
        "payment_terms": str(extracted_data.get("payment_terms") or ""),
        "purchase_order_number": str(extracted_data.get("purchase_order_number") or ""),
        "notes": str(extracted_data.get("notes") or ""),
        "bank_details": {
            "account_number": str(bank.get("account_number") or ""),
            "account_holder": str(bank.get("account_holder") or ""),
            "bank_name": str(bank.get("bank_name") or ""),
            "ifsc": str(bank.get("ifsc") or ""),
            "branch": str(bank.get("branch") or ""),
        },
        "line_items": extracted_data.get("line_items") or [],
    }


@router.get("/invoice/{invoice_id}")
async def get_erp_invoice(
    invoice_id: str,
    current_user: UserOut = Depends(get_current_user),
):
    global CURRENT_HANDOFF_INVOICE_ID
    CURRENT_HANDOFF_INVOICE_ID = invoice_id
    invoice = await invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise NotFoundException(f"Invoice {invoice_id} not found.")

    return _format_erp_payload(invoice.id, invoice.extracted_data or {})


@router.post("/set_current_invoice")
async def set_current_invoice(
    req: SetCurrentInvoiceRequest,
    current_user: UserOut = Depends(get_current_user),
):
    global CURRENT_HANDOFF_INVOICE_ID
    invoice = await invoice_repo.get_by_id(req.invoice_id)
    if not invoice:
        raise NotFoundException(f"Invoice {req.invoice_id} not found.")

    CURRENT_HANDOFF_INVOICE_ID = req.invoice_id
    return {"message": "Current invoice set successfully", "invoice_id": req.invoice_id}


@router.get("/get_current_invoice")
async def get_current_invoice(
    current_user: UserOut = Depends(get_current_user),
):
    global CURRENT_HANDOFF_INVOICE_ID
    if not CURRENT_HANDOFF_INVOICE_ID:
        # Fallback to latest invoice in repo
        all_invoices = await invoice_repo.list_all(limit=1)
        if all_invoices:
            CURRENT_HANDOFF_INVOICE_ID = all_invoices[0].id
        else:
            raise NotFoundException("No current invoice is set.")

    invoice = await invoice_repo.get_by_id(CURRENT_HANDOFF_INVOICE_ID)
    if not invoice:
        raise NotFoundException("Current invoice not found.")

    return _format_erp_payload(invoice.id, invoice.extracted_data or {})


@router.post("/save_erp")
async def save_erp_invoice(
    payload: ERPInvoiceSave,
    current_user: UserOut = Depends(get_current_user),
):
    erp_record = await erp_invoice_repo.save(payload.data, source_invoice_id=payload.source_invoice_id)
    return {"message": "ERP invoice saved successfully", "erp_record": erp_record}
