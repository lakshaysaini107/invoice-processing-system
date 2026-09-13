from typing import Any, Dict, Tuple


class ConfidenceScorer:
    def calculate_scores(self, extracted_data: Dict[str, Any], ocr_lines: list) -> Tuple[float, Dict[str, float]]:
        field_scores = {}

        # Base OCR average confidence
        ocr_confs = [l.get("confidence", 0.8) for l in ocr_lines if isinstance(l, dict)]
        base_ocr_conf = float(sum(ocr_confs) / len(ocr_confs)) if ocr_confs else 0.75

        fields = [
            ("invoice_number", 0.95),
            ("invoice_date", 0.90),
            ("vendor_name", 0.85),
            ("vendor_gst", 0.95),
            ("total_amount", 0.95),
            ("tax_amount", 0.85),
            ("buyer_name", 0.80),
            ("bank_details", 0.80),
            ("line_items", 0.85),
        ]

        for field, weight in fields:
            val = extracted_data.get(field)
            if val:
                if isinstance(val, dict):
                    has_val = any(v for v in val.values() if v)
                    field_scores[field] = round(base_ocr_conf * weight, 2) if has_val else 0.0
                elif isinstance(val, list):
                    field_scores[field] = round(base_ocr_conf * weight, 2) if len(val) > 0 else 0.0
                else:
                    field_scores[field] = round(base_ocr_conf * weight, 2)
            else:
                field_scores[field] = 0.0

        present_scores = [s for s in field_scores.values() if s > 0]
        overall_confidence = float(sum(present_scores) / len(present_scores)) if present_scores else 0.0

        return round(overall_confidence, 2), field_scores


confidence_scorer = ConfidenceScorer()
