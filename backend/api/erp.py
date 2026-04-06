from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.app.dependencies import (
    get_erp_current_invoice_store,
    get_erp_invoice_repository,
    get_invoice_repository,
)
from backend.database.repositories.erp_invoice_repo import ERPInvoiceRepository
from backend.database.repositories.invoice_repo import InvoiceRepository


router = APIRouter(prefix="/api/erp", tags=["erp"])


class ERPSetCurrentInvoiceRequest(BaseModel):
    invoice_id: Optional[str] = None


class ERPSaveRequest(BaseModel):
    source_invoice_id: Optional[str] = None
    data: Dict[str, Any]


def _build_erp_payload(invoice: Dict[str, Any]) -> Dict[str, Any]:
    extracted_data = invoice.get("extracted_data") if isinstance(invoice.get("extracted_data"), dict) else {}
    payload = deepcopy(extracted_data)
    if not isinstance(payload.get("bank_details"), dict):
        payload["bank_details"] = {
            "account_number": None,
            "account_holder": None,
            "bank_name": None,
            "ifsc": None,
            "branch": None,
        }
    if not isinstance(payload.get("line_items"), list):
        payload["line_items"] = []
    payload["source_invoice_id"] = invoice.get("invoice_id")
    payload["filename"] = invoice.get("filename")
    payload["review_status"] = invoice.get("review_status")
    payload["processing_status"] = invoice.get("processing_status")
    return payload


async def _resolve_erp_invoice(
    invoice_repo: InvoiceRepository,
    invoice_id: Optional[str],
) -> Optional[Dict[str, Any]]:
    if invoice_id:
        return await invoice_repo.get_by_id(invoice_id)

    invoices = await invoice_repo.list_recent(skip=0, limit=50)
    invoice = next(
        (
            item for item in invoices
            if str(item.get("review_status") or "").lower() == "approved"
            and isinstance(item.get("extracted_data"), dict)
        ),
        None,
    )
    if invoice is None:
        invoice = next(
            (
                item for item in invoices
                if str(item.get("processing_status") or "").lower() in {"completed", "reviewed"}
                and isinstance(item.get("extracted_data"), dict)
            ),
            None,
        )
    return invoice


@router.post("/set_current_invoice")
async def set_current_invoice(
    request: ERPSetCurrentInvoiceRequest,
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository),
    current_invoice_store: Dict[str, Any] = Depends(get_erp_current_invoice_store),
):
    invoice_id = request.invoice_id
    invoice = await _resolve_erp_invoice(invoice_repo, invoice_id)

    if invoice is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No reviewed invoice is available for ERP handoff.",
        )

    if not isinstance(invoice.get("extracted_data"), dict) or not invoice.get("extracted_data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invoice does not have extracted review data yet.",
        )

    current_invoice_store.clear()
    current_invoice_store.update(_build_erp_payload(invoice))
    return {
        "status": "ok",
        "invoice_id": invoice.get("invoice_id"),
    }


@router.get("/get_current_invoice")
async def get_current_invoice(
    current_invoice_store: Dict[str, Any] = Depends(get_erp_current_invoice_store),
):
    if not current_invoice_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No current invoice has been sent to ERP yet.",
        )
    return deepcopy(current_invoice_store)


@router.get("/invoice/{invoice_id}")
async def get_invoice_for_erp(
    invoice_id: str,
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository),
):
    invoice = await invoice_repo.get_by_id(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found.",
        )

    if not isinstance(invoice.get("extracted_data"), dict) or not invoice.get("extracted_data"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invoice does not have extracted review data yet.",
        )

    return _build_erp_payload(invoice)


@router.post("/save_erp")
async def save_erp(
    request: ERPSaveRequest,
    erp_repo: ERPInvoiceRepository = Depends(get_erp_invoice_repository),
):
    saved = await erp_repo.save(
        source_invoice_id=request.source_invoice_id,
        data=request.data,
    )
    return {
        "status": "saved",
        "erp_record": saved,
    }
