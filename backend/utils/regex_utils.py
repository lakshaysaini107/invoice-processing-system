import re
from typing import Dict, List

REGEX_PATTERNS: Dict[str, str] = {
    # GST - Indian GST format (tolerant to common OCR confusions like O/0 or I/1)
    "gst": r"\b[0-9OIL]{2}[A-Z]{5}[0-9OIL]{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9OIL]{1}\b",

    # Invoice Number
    "invoice_number": r"^[A-Z0-9\-\/]{3,20}$",

    # Amount formats with or without currency
    "amount": r"(?:Rs\.?|INR|\u20B9|\$|USD|EUR|\u20AC)?\s*((?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?)",

    # Date formats (numeric or month names)
    "date": r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{1,2}[-/][A-Za-z]{3,9}[-/]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4})",

    # Email
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",

    # Phone (Indian format)
    "phone": r"(?:\+91[-.\s]?)?\d{10}",

    # Account Number (9-18 digits)
    "account_number": r"\b\d{9,18}\b",

    # IFSC Code
    "ifsc": r"[A-Z]{4}0[A-Z0-9]{6}",

    # PAN (Permanent Account Number)
    "pan": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",

    # Aadhar Number
    "aadhar": r"\d{4}\s\d{4}\s\d{4}",

    # URL
    "url": r"https?://[^\s]+",
}

def match_pattern(pattern_name: str, text: str) -> bool:
    """Check if text matches pattern"""
    pattern = REGEX_PATTERNS.get(pattern_name)
    if not pattern:
        return False
    return bool(re.search(pattern, text, re.IGNORECASE))

def extract_by_pattern(pattern_name: str, text: str) -> List[str]:
    """Extract all matches for a pattern"""
    pattern = REGEX_PATTERNS.get(pattern_name)
    if not pattern:
        return []

    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches

def validate_email(email: str) -> bool:
    """Validate email address"""
    return match_pattern("email", email)

def validate_phone(phone: str) -> bool:
    """Validate phone number"""
    return match_pattern("phone", phone)

def validate_ifsc(ifsc: str) -> bool:
    """Validate IFSC code"""
    return match_pattern("ifsc", ifsc.upper())

def validate_pan(pan: str) -> bool:
    """Validate PAN"""
    return match_pattern("pan", pan.upper())

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace"""
    return re.sub(r'\s+', ' ', text.strip())

def extract_numbers(text: str) -> List[str]:
    """Extract all numbers from text"""
    return re.findall(r'\d+', text)
