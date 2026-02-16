from typing import Dict, Any, List
from datetime import datetime
from backend.core.logging import logger

class ReviewService:
    """Handle manual review corrections and approvals"""

    def __init__(self):
        pass

    async def apply_corrections(
        self,
        extracted_data: dict,
        corrections: List
    ) -> dict:
        """Apply user corrections to extracted data"""
        
        corrected_data = extracted_data.copy()
        
        for correction in corrections:
            field_name = correction.field_name
            corrected_value = correction.corrected_value
            
            # Apply correction
            corrected_data[field_name] = corrected_value
            
            logger.info(
                f"Field {field_name} corrected: "
                f"{correction.original_value} → {corrected_value}"
            )
            
        return corrected_data

    async def get_high_risk_fields(
        self,
        extracted_data: dict,
        confidence_scores: dict
    ) -> List[str]:
        """Identify fields requiring manual review (confidence < 0.7)"""
        
        high_risk = []
        
        for field_name, confidence_info in confidence_scores.items():
            if field_name != "overall" and confidence_info.get("requires_review"):
                high_risk.append({
                    "field": field_name,
                    "value": extracted_data.get(field_name),
                    "confidence": confidence_info.get("confidence"),
                    "reason": "Low confidence score"
                })
        
        return high_risk

    async def generate_review_summary(
        self,
        invoice_id: str,
        extracted_data: dict,
        confidence_scores: dict
    ) -> dict:
        """Generate summary for review interface"""
        
        high_risk = await self.get_high_risk_fields(extracted_data, confidence_scores)
        
        return {
            "invoice_id": invoice_id,
            "total_fields": len(extracted_data),
            "high_confidence_fields": len([
                f for f, v in confidence_scores.items()
                if f != "overall" and v.get("confidence", 0) >= 0.85
            ]),
            "medium_confidence_fields": len([
                f for f, v in confidence_scores.items()
                if f != "overall" and 0.7 <= v.get("confidence", 0) < 0.85
            ]),
            "low_confidence_fields": len(high_risk),
            "requires_review": len(high_risk) > 0,
            "overall_confidence": confidence_scores.get("overall", 0),
            "fields_needing_attention": high_risk
        }
