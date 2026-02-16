from typing import Dict, Any, List, Optional
import re
from backend.core.logging import logger
from backend.utils.regex_utils import REGEX_PATTERNS

class ConfidenceScoringEngine:
    """
    Calculate confidence scores for extracted fields based on multiple factors:
    1. OCR confidence (from Tesseract/PaddleOCR)
    2. Pattern matching (Regex validation)
    3. LLM certainty (if provided)
    4. Business rule validation
    """

    def __init__(self):
        # Weights for different factors
        self.weights = {
            "ocr": 0.3,
            "pattern": 0.4,
            "llm": 0.3
        }

    async def calculate_scores(
        self,
        extracted_data: Dict[str, Any],
        ocr_result: Dict[str, Any],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate individual and overall confidence scores.
        
        Args:
            extracted_data: JSON data extracted by LLM
            ocr_result: Raw OCR result with box-level confidence
            validation_results: Results from validation service
            
        Returns:
            Dict containing field-level scores and overall document score
        """
        scores = {}
        total_score = 0
        field_count = 0

        try:
            # Calculate score for each field
            for field, value in extracted_data.items():
                if field in ["line_items", "bank_details"]:
                    # Handle complex nested objects separately
                    field_score = await self._score_complex_field(field, value, ocr_result)
                else:
                    # Handle simple key-value fields
                    field_score = await self._score_simple_field(
                        field, value, ocr_result, validation_results.get(field)
                    )
                
                scores[field] = {
                    "value": value,
                    "confidence": round(field_score, 2),
                    "status": "high" if field_score > 0.8 else "low" if field_score < 0.5 else "medium"
                }
                
                total_score += field_score
                field_count += 1

            # Calculate overall document confidence
            overall_confidence = total_score / field_count if field_count > 0 else 0.0
            
            # Add metadata
            scores["overall_score"] = round(overall_confidence, 2)
            scores["ocr_quality"] = round(ocr_result.get("average_confidence", 0.0), 2)
            
            return scores

        except Exception as e:
            logger.error(f"Error calculating confidence scores: {str(e)}")
            # Return default low scores on error
            return {"overall_score": 0.0, "error": str(e)}

    async def _score_simple_field(
        self,
        field_name: str,
        value: Any,
        ocr_result: Dict[str, Any],
        validation_result: Optional[Dict] = None
    ) -> float:
        """Score a single scalar field (string, number, date)"""
        
        if not value:
            return 0.0

        score = 0.0
        
        # 1. OCR Confidence (Check if value exists in raw OCR text with high confidence)
        ocr_conf = self._check_ocr_presence(str(value), ocr_result)
        score += ocr_conf * self.weights["ocr"]
        
        # 2. Pattern Matching (Regex)
        pattern_conf = self._check_pattern_match(field_name, str(value))
        score += pattern_conf * self.weights["pattern"]
        
        # 3. Validation Logic (from ValidationService)
        # If validation passed, boost the score
        if validation_result and validation_result.get("is_valid"):
            score += 0.3 # Boost for passing business rules
        elif validation_result and not validation_result.get("is_valid"):
            score -= 0.2 # Penalty for failing business rules
            
        return min(max(score, 0.0), 1.0) # Clamp between 0 and 1

    async def _score_complex_field(
        self,
        field_name: str,
        value: Any,
        ocr_result: Dict[str, Any]
    ) -> float:
        """Score complex fields like line items or bank details"""
        
        if not value:
            return 0.0
            
        if isinstance(value, list): # Line items
            if not value:
                return 0.0
            # Average score of all items in the list
            item_scores = []
            for item in value:
                # Simple heuristic: check if description and total exist
                if isinstance(item, dict):
                    desc_score = self._check_ocr_presence(item.get("description", ""), ocr_result)
                    price_score = 1.0 if item.get("total") else 0.0
                    item_scores.append((desc_score + price_score) / 2)
            
            return sum(item_scores) / len(item_scores) if item_scores else 0.0

        elif isinstance(value, dict): # Bank details
            # Check for key fields like Account No and IFSC
            acc_score = self._check_pattern_match("account_number", value.get("account_number", ""))
            ifsc_score = self._check_pattern_match("ifsc", value.get("ifsc", ""))
            return (acc_score + ifsc_score) / 2
            
        return 0.5 # Default for unknown types

    def _check_ocr_presence(self, text: str, ocr_result: Dict[str, Any]) -> float:
        """Check if text is present in OCR results and return its confidence"""
        if not text:
            return 0.0
            
        # Search for the text in OCR boxes
        # This is a simplified O(N) search. For production, use an index.
        text_lower = text.lower()
        
        best_conf = 0.0
        found = False
        
        for box in ocr_result.get("boxes", []):
            if text_lower in box["text"].lower():
                best_conf = max(best_conf, box.get("confidence", 0.0))
                found = True
        
        # If exact match found in boxes, return box confidence
        if found:
            return best_conf
            
        # If not found in boxes but present in full text (maybe split across boxes)
        if text_lower in ocr_result.get("text", "").lower():
            return 0.7 # Lower confidence if not an exact box match
            
        return 0.0

    def _check_pattern_match(self, field_name: str, value: str) -> float:
        """Check if value matches expected regex pattern for the field"""
        if not value:
            return 0.0
            
        pattern = None
        
        # Map field names to regex patterns
        if "email" in field_name:
            pattern = REGEX_PATTERNS.get("email")
        elif "gst" in field_name:
            pattern = REGEX_PATTERNS.get("gst")
        elif "date" in field_name:
            pattern = REGEX_PATTERNS.get("date")
        elif "amount" in field_name or "total" in field_name or "price" in field_name:
            pattern = REGEX_PATTERNS.get("amount")
        elif "ifsc" in field_name:
            pattern = r"^[A-Z]{4}0[A-Z0-9]{6}$"
        elif "pan" in field_name:
            pattern = REGEX_PATTERNS.get("pan")
            
        if pattern:
            if re.match(pattern, value, re.IGNORECASE):
                return 1.0
            return 0.2 # Penalty for pattern mismatch
            
        return 0.5 # Neutral score if no pattern defined
