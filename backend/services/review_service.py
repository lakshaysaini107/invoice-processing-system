from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.core.exceptions import NotFoundException
from backend.database.repositories.invoice_repo import invoice_repo
from backend.models.inoice import InvoiceOut, ProcessingStatus, ReviewStatus


class ReviewService:
    async def submit_review(
        self,
        invoice_id: str,
        updated_extracted_data: Dict[str, Any],
        review_status: str = ReviewStatus.APPROVED.value,
        review_notes: Optional[str] = None,
        reviewed_by: Optional[str] = "reviewer",
    ) -> InvoiceOut:
        existing = await invoice_repo.get_by_id(invoice_id)
        if not existing:
            raise NotFoundException(f"Invoice {invoice_id} not found.")

        old_data = existing.extracted_data or {}
        corrections: List[Dict[str, Any]] = existing.corrections or []

        for field, new_val in updated_extracted_data.items():
            old_val = old_data.get(field)
            if old_val != new_val:
                corrections.append({
                    "field": field,
                    "old_value": old_val,
                    "new_value": new_val,
                    "timestamp": datetime.utcnow().isoformat(),
                    "reviewed_by": reviewed_by,
                })

        updates = {
            "extracted_data": updated_extracted_data,
            "corrections": corrections,
            "review_status": review_status,
            "processing_status": ProcessingStatus.REVIEWED.value,
            "reviewed_by": reviewed_by,
            "reviewed_at": datetime.utcnow(),
            "review_notes": review_notes,
        }
        return await invoice_repo.update(invoice_id, updates)


review_service = ReviewService()
