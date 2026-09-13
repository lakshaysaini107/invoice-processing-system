from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEWED = "reviewed"


class ReviewStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    APPROVED = "approved"
    MODIFIED = "modified"
    REJECTED = "rejected"


class BankDetails(BaseModel):
    account_number: Optional[str] = None
    account_holder: Optional[str] = None
    bank_name: Optional[str] = None
    ifsc: Optional[str] = None
    branch: Optional[str] = None


class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    amount: Optional[float] = None
    hsn_sac: Optional[str] = None
    tax_rate: Optional[float] = None


class InvoiceExtractedData(BaseModel):
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
    notes: Optional[str] = None
    bank_details: Optional[BankDetails] = Field(default_factory=BankDetails)
    line_items: List[LineItem] = Field(default_factory=list)


class InvoiceCreate(BaseModel):
    filename: str
    file_path: str
    file_size: int
    user_id: Optional[str] = "default_user"


class InvoiceReviewSubmit(BaseModel):
    extracted_data: Dict[str, Any]
    review_status: Optional[str] = "approved"
    review_notes: Optional[str] = None


class ERPInvoiceSave(BaseModel):
    source_invoice_id: Optional[str] = None
    data: Dict[str, Any]


class InvoiceOut(BaseModel):
    id: str
    user_id: Optional[str] = "default_user"
    filename: str
    file_path: str
    file_size: int
    upload_timestamp: Optional[datetime] = None
    processing_status: str = ProcessingStatus.PENDING.value
    overall_confidence: float = 0.0
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    confidence_scores: Dict[str, Any] = Field(default_factory=dict)
    ocr_result: Dict[str, Any] = Field(default_factory=dict)
    layout_info: Dict[str, Any] = Field(default_factory=dict)
    entities: Dict[str, Any] = Field(default_factory=dict)
    corrections: List[Dict[str, Any]] = Field(default_factory=list)
    review_status: str = ReviewStatus.UNREVIEWED.value
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    error_message: Optional[str] = None
