from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
import uuid
from datetime import datetime
from backend.core.security import get_current_user
from backend.services.upload_service import UploadService
from backend.database.repositories.invoice_repo import InvoiceRepository
from backend.core.logging import logger
from backend.app.dependencies import get_upload_service, get_invoice_repository

router = APIRouter(prefix="/invoices", tags=["invoice-upload"])

# ==================== Schemas ====================

class UploadResponse(BaseModel):
    invoice_id: str
    filename: str
    upload_time: datetime
    status: str = "uploaded"
    message: str

class InvoiceListResponse(BaseModel):
    invoice_id: str
    filename: str
    upload_time: datetime
    status: str
    pages: int = 1

# ==================== Endpoints ====================

@router.post("/upload", response_model=UploadResponse)
async def upload_invoice(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """
    Upload one or multiple invoice files (PDF, JPG, PNG)
    Supported formats: PDF, JPEG, PNG, TIFF
    Max file size: 20MB per file
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )

    results = []
    
    for file in files:
        try:
            # Validate file
            await upload_service.validate_file(file)
            
            # Generate unique invoice ID
            invoice_id = str(uuid.uuid4())
            
            # Save file
            file_path = await upload_service.save_file(
                file=file,
                invoice_id=invoice_id,
                user_id=current_user["_id"]
            )
            
            # Create invoice record in database
            file_info = await upload_service.get_file_info(file_path)
            invoice_data = {
                "invoice_id": invoice_id,
                "user_id": current_user["_id"],
                "filename": file.filename,
                "file_path": file_path,
                "file_size": file_info["size"],
                "status": "uploaded",
                "upload_time": datetime.utcnow(),
                "processing_status": "pending",
                "extracted_data": None,
                "confidence_scores": None
            }
            
            await invoice_repo.create(invoice_data)
            
            results.append(UploadResponse(
                invoice_id=invoice_id,
                filename=file.filename,
                upload_time=datetime.utcnow(),
                status="uploaded",
                message=f"File {file.filename} uploaded successfully"
            ))
            
            logger.info(f"Invoice {invoice_id} uploaded by user {current_user['_id']}")
            
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )
    
    # Return first result if single file, usually managed by frontend
    return results[0]

@router.get("/list", response_model=List[InvoiceListResponse])
async def list_invoices(
    current_user: dict = Depends(get_current_user),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository),
    skip: int = 0,
    limit: int = 20
):
    """Get user's invoice list with pagination"""
    invoices = await invoice_repo.get_by_user(
        user_id=current_user["_id"],
        skip=skip,
        limit=limit
    )

    return [
        InvoiceListResponse(
            invoice_id=inv["invoice_id"],
            filename=inv["filename"],
            upload_time=inv["upload_time"],
            status=inv.get("processing_status", inv.get("status", "uploaded")),
            pages=inv.get("pages", 1)
        )
        for inv in invoices
    ]

@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    current_user: dict = Depends(get_current_user),
    upload_service: UploadService = Depends(get_upload_service),
    invoice_repo: InvoiceRepository = Depends(get_invoice_repository)
):
    """Delete an uploaded invoice"""
    invoice = await invoice_repo.get_by_id(invoice_id)

    if not invoice or invoice["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    
    # Delete file from storage
    await upload_service.delete_file(invoice["file_path"])
    
    # Delete from database
    await invoice_repo.delete(invoice_id)
    
    logger.info(f"Invoice {invoice_id} deleted by user {current_user['_id']}")
    
    return {"message": "Invoice deleted successfully"}
