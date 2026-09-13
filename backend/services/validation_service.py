from typing import Any, Dict, Tuple
from backend.ai.confidence_scoring import confidence_scorer
from backend.utils.date_utils import parse_date
from backend.utils.gst_utils import normalize_gstin
from backend.utils.math_utils import parse_amount


class ValidationService:
    def validate_and_score(
        self, extracted_data: Dict[str, Any], ocr_lines: list
    ) -> Tuple[Dict[str, Any], float, Dict[str, float]]:
        cleaned_data = extracted_data.copy()

        # Normalize dates
        if cleaned_data.get("invoice_date"):
            cleaned_data["invoice_date"] = parse_date(cleaned_data["invoice_date"])
        if cleaned_data.get("due_date"):
            cleaned_data["due_date"] = parse_date(cleaned_data["due_date"])

        # Normalize GST
        if cleaned_data.get("vendor_gst"):
            cleaned_data["vendor_gst"] = normalize_gstin(cleaned_data["vendor_gst"])
        if cleaned_data.get("buyer_gst"):
            cleaned_data["buyer_gst"] = normalize_gstin(cleaned_data["buyer_gst"])

        # Normalize amounts
        if cleaned_data.get("total_amount") is not None:
            cleaned_data["total_amount"] = parse_amount(cleaned_data["total_amount"])
        if cleaned_data.get("invoice_amount") is not None:
            cleaned_data["invoice_amount"] = parse_amount(cleaned_data["invoice_amount"])
        if cleaned_data.get("tax_amount") is not None:
            cleaned_data["tax_amount"] = parse_amount(cleaned_data["tax_amount"])

        overall_confidence, field_scores = confidence_scorer.calculate_scores(cleaned_data, ocr_lines)
        return cleaned_data, overall_confidence, field_scores


validation_service = ValidationService()
