import re

# Indian GSTIN pattern
GSTIN_PATTERN = r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}\b"

# Invoice Number patterns
INVOICE_NO_PATTERNS = [
    r"(?i)\binvoice\s*(?:no|num|number|#|\.)?[:\s]*([A-Z0-9/-]{3,30})\b",
    r"(?i)\binv\s*(?:no|num|number|#|\.)?[:\s]*([A-Z0-9/-]{3,30})\b",
    r"(?i)\bbill\s*(?:no|num|number|#|\.)?[:\s]*([A-Z0-9/-]{3,30})\b",
]

# Date patterns (DD/MM/YYYY, YYYY-MM-DD, DD-MMM-YYYY, etc.)
DATE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
    r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}\b",
]

# Currency / Amount patterns
AMOUNT_PATTERN = r"(?:₹|Rs\.?|INR)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?)"

# PO Number pattern
PO_PATTERNS = [
    r"(?i)\bpo\s*(?:no|num|number|#|\.)?[:\s]*([A-Z0-9/-]{3,30})\b",
    r"(?i)\bpurchase\s*order\s*(?:no|num|number|#|\.)?[:\s]*([A-Z0-9/-]{3,30})\b",
]

# IFSC pattern
IFSC_PATTERN = r"\b[A-Z]{4}0[A-Z0-9]{6}\b"

# Bank Account pattern
ACCOUNT_NO_PATTERN = r"\b\d{9,18}\b"
