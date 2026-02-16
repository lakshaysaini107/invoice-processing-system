from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWED = "reviewed"

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class LineItem(BaseModel):
    description: str
    quantity: float
    unit: str
    unit_price: float
    total: float

class BankDetails(BaseModel):
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc: Optional[str] = None
    branch: Optional[str] = None

class ExtractedInvoiceData(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_gst: Optional[str] = None
    vendor_address: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_gst: Optional[str] = None
    buyer_address: Optional[str] = None
    invoice_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    total_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    currency: Optional[str] = "INR"
    payment_terms: Optional[str] = None
    purchase_order_number: Optional[str] = None
    line_items: Optional[List[LineItem]] = []
    bank_details: Optional[BankDetails] = None
    notes: Optional[str] = None

class ConfidenceScore(BaseModel):
    field_name: str
    confidence: float
    is_valid: bool
    requires_review: bool
    status: str  # "high", "medium", "low"

class Invoice(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    invoice_id: str
    user_id: str
    filename: str
    file_path: str
    file_size: int
    status: str = "uploaded"
    upload_time: datetime
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    review_status: Optional[ReviewStatus] = None
    
    # Processing fields
    progress: int = 0
    current_step: Optional[str] = None
    step_description: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Extraction results
    extracted_data: Optional[ExtractedInvoiceData] = None
    confidence_scores: Optional[Dict[str, ConfidenceScore]] = None
    ocr_result: Optional[Dict[str, Any]] = None
    layout_info: Optional[Dict[str, Any]] = None
    entities: Optional[Dict[str, Any]] = None
    
    # Review fields
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    corrections: Optional[List[Dict[str, Any]]] = None
    review_notes: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
