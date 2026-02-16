from typing import Tuple, Dict, Any, List
from backend.core.logging import logger
# Ensure you have these utility modules or mock them
from backend.utils.gst_utils import validate_gst, parse_gst
from backend.utils.date_utils import validate_date, parse_date
from backend.utils.math_utils import parse_amount
import re

class ValidationService:
    """Validate extracted fields and assign confidence scores"""

    def __init__(self):
        self.field_validators = {
            "invoice_number": self._validate_invoice_number,
            "invoice_date": self._validate_date,
            "due_date": self._validate_date,
            "vendor_name": self._validate_name,
            "vendor_gst": self._validate_gst,
            "buyer_name": self._validate_name,
            "buyer_gst": self._validate_gst,
            "invoice_amount": self._validate_amount,
            "tax_amount": self._validate_amount,
            "total_amount": self._validate_amount,
            "payment_terms": self._validate_payment_terms,
            "bank_details": self._validate_bank_details
        }

    async def validate_extraction(
        self,
        extracted_fields: dict,
        entities: dict,
        raw_text: str
    ) -> Tuple[dict, dict]:
        """
        Validate all extracted fields and calculate confidence scores
        Returns: (validated_data, confidence_scores)
        """
        validated_data = {}
        confidence_scores = {}

        # Validate each field
        for field_name, field_value in extracted_fields.items():
            validator = self.field_validators.get(
                field_name,
                self._default_validator
            )
            
            is_valid, confidence, corrected_value = await validator(field_value, raw_text)
            
            validated_data[field_name] = corrected_value if is_valid else field_value
            confidence_scores[field_name] = {
                "is_valid": is_valid,
                "confidence": confidence,
                "requires_review": confidence < 0.7
            }

        # Calculate overall confidence
        confidences = [v["confidence"] for v in confidence_scores.values()]
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        confidence_scores["overall"] = overall_confidence
        
        logger.info(f"Validation complete - Overall confidence: {overall_confidence:.2%}")
        
        return validated_data, confidence_scores

    async def _validate_invoice_number(self, value: str, raw_text: str) -> Tuple[bool, float, str]:
        """Validate invoice number format"""
        if not value:
            return False, 0.0, None
        
        # Pattern: INV-YYYY-XXXXX or similar
        # Simple heuristic check
        if re.match(r"^[A-Z0-9\-\/]{3,20}$", str(value).strip()):
            # Check if number appears multiple times (likely correct)
            occurrences = raw_text.lower().count(str(value).lower())
            confidence = min(0.9 + (occurrences * 0.05), 1.0)
            return True, confidence, str(value).strip()
        
        return False, 0.3, value

    async def _validate_date(self, value: str, raw_text: str) -> Tuple[bool, float, str]:
        """Validate date format"""
        if not value:
            return False, 0.0, None
        
        try:
            parsed_date = parse_date(str(value)) # Needs implementation in utils
            if parsed_date:
                return True, 0.95, parsed_date
            return False, 0.2, value
        except:
            return False, 0.1, value

    async def _validate_gst(self, value: str, raw_text: str) -> Tuple[bool, float, str]:
        """Validate GST number"""
        if not value:
            return False, 0.0, None
        
        try:
            is_valid = validate_gst(str(value)) # Needs implementation in utils
            if is_valid:
                parsed_gst = parse_gst(str(value))
                return True, 0.98, parsed_gst
            return False, 0.1, value
        except:
            return False, 0.05, value

    async def _validate_name(self, value: str, raw_text: str) -> Tuple[bool, float, str]:
        """Validate company/person name"""
        if not value or len(str(value).strip()) < 2:
            return False, 0.0, None
        
        # Check if name appears multiple times
        occurrences = raw_text.lower().count(str(value).lower())
        confidence = min(0.7 + (occurrences * 0.05), 0.95)
        
        return True, confidence, str(value).strip()

    async def _validate_amount(self, value: Any, raw_text: str) -> Tuple[bool, float, float]:
        """Validate numeric amount"""
        if value is None:
            return False, 0.0, None
        
        try:
            amount = parse_amount(value) # Needs implementation in utils
            if amount and amount > 0:
                return True, 0.95, amount
            return False, 0.2, value
        except:
            return False, 0.1, value

    async def _validate_payment_terms(self, value: str, raw_text: str) -> Tuple[bool, float, str]:
        """Validate payment terms"""
        if not value:
            return False, 0.0, None
        
        # Common patterns: NET30, Due on demand, etc.
        if re.search(r"(net|due|payment|credit).*?(\d+|on\s+demand)", str(value).lower()):
            return True, 0.85, str(value).strip()
        
        return False, 0.4, value

    async def _validate_bank_details(self, value: dict, raw_text: str) -> Tuple[bool, float, dict]:
        """Validate bank account details"""
        if not value:
            return False, 0.0, None
        
        account_no = str(value.get("account_number", ""))
        ifsc = str(value.get("ifsc", ""))
        
        # Basic validation
        if len(account_no) >= 9 and len(ifsc) == 11:
            return True, 0.90, value
        
        return False, 0.3, value

    async def _default_validator(self, value: Any, raw_text: str) -> Tuple[bool, float, Any]:
        """Default validation for unmapped fields"""
        if value:
            return True, 0.5, value
        return False, 0.0, None
