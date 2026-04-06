from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List
import io
from backend.core.security import get_current_user
from backend.services.export_service import ExportService
from backend.database.repositories.invoice_repo import InvoiceRepository
from backend.core.logging import logger
from backend.app.dependencies import get_export_service, get_invoice_repository

router = APIRouter(prefix="/export", tags=["export"])

# ==================== Schemas ====================

class ExportRequest(BaseModel):
    invoice_ids: List[str]
    format: str # "json", "csv", "excel"
    include_confidence: bool = False

# ==================== Endpoints ====================

@router.post("/single/{invoice_id}")
async def export_single_invoice(
    invoice_id: str,
    format: str = "json", # json, csv, excel
    current_user: dict = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """Export single invoice in requested format"""
    invoice = await invoice_repo.get_by_id(invoice_id)

    if not invoice or invoice["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    if format not in ["json", "csv", "excel"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Choose from: json, csv, excel"
        )
    
    try:
        if format == "json":
            content = await export_service.to_json(invoice)
            return {
                "filename": f"{invoice['filename'].split('.')[0]}.json",
                "data": content
            }
        
        elif format == "csv":
            csv_content = await export_service.to_csv([invoice])
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={invoice_id}.csv"}
            )
            
        elif format == "excel":
            excel_bytes = await export_service.to_excel([invoice])
            return StreamingResponse(
                iter([excel_bytes.getvalue()]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={invoice_id}.xlsx"}
            )
            
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.post("/batch")
async def export_batch(
    request: ExportRequest,
    current_user: dict = Depends(get_current_user),
    export_service: ExportService = Depends(get_export_service),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """Batch export multiple invoices"""
    invoices = []
    
    for invoice_id in request.invoice_ids:
        invoice = await invoice_repo.get_by_id(invoice_id)
        if invoice and invoice["user_id"] == current_user["_id"]:
            invoices.append(invoice)
    
    if not invoices:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid invoices found"
        )
        
    try:
        if request.format == "json":
            content = await export_service.batch_to_json(invoices)
            return {"data": content}
            
        elif request.format == "csv":
            csv_content = await export_service.to_csv(invoices)
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=invoices_export.csv"}
            )
            
        elif request.format == "excel":
            excel_bytes = await export_service.to_excel(invoices)
            return StreamingResponse(
                iter([excel_bytes.getvalue()]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=invoices_export.xlsx"}
            )
            
    except Exception as e:
        logger.error(f"Batch export error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.get("/template/fields")
async def get_export_template():
    """Get available fields for export"""
    return {
        "invoice_fields": [
            "invoice_number",
            "invoice_date",
            "due_date",
            "vendor_name",
            "vendor_gst",
            "buyer_name",
            "buyer_gst",
            "invoice_amount",
            "tax_amount",
            "total_amount",
            "payment_terms",
            "line_items",
            "bank_details"
        ],
        "metadata_fields": [
            "upload_time",
            "processing_time",
            "reviewed_at",
            "review_status",
            "confidence_scores"
        ]
    }
