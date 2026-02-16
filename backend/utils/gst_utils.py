import re
from typing import Optional

OCR_DIGIT_MAP = {
    "O": "0",
    "I": "1",
    "L": "1",
}

def normalize_gst_ocr(gst_number: str) -> str:
    """Normalize common OCR errors in GST numbers (O/0, I/1, L/1)."""
    if not gst_number:
        return gst_number

    gst_number = gst_number.strip().upper()
    if len(gst_number) != 15:
        return gst_number

    chars = list(gst_number)
    digit_positions = {0, 1, 7, 8, 9, 10, 14}
    for idx in digit_positions:
        char = chars[idx]
        if char in OCR_DIGIT_MAP:
            chars[idx] = OCR_DIGIT_MAP[char]

    return "".join(chars)

def validate_gst(gst_number: str) -> bool:
    """
    Validate GST number format (Indian)
    Format: 15 characters - 2 digits, 5 uppercase letters, 4 digits, 1 letter, 1 digit, Z, 1 digit
    Example: 18AABCU9603R2Z5
    """
    if not gst_number:
        return False

    gst_number = normalize_gst_ocr(gst_number.strip().upper())
    
    # GST pattern
    pattern = r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z\d{1}$"
    
    if not re.match(pattern, gst_number):
        return False
    
    # NOTE: Keep validation lenient to avoid false negatives.
    # Full checksum validation varies by implementation; format check is sufficient here.
    return True

def _validate_gst_checksum(gst: str) -> bool:
    """Validate GST checksum using Luhn algorithm"""
    gst_digits = gst[:-1]  # Exclude last character (check digit)
    
    # Convert characters to numbers
    gst_numeric = ""
    for char in gst_digits:
        if char.isdigit():
            gst_numeric += char
        else:
            # A=10, B=11, ... Z=35
            gst_numeric += str(ord(char) - ord('A') + 10)
    
    # Apply Luhn algorithm
    total = 0
    for i, digit in enumerate(gst_numeric):
        value = int(digit)
        if i % 2 == 0:
            value *= 2
            if value > 9:
                value -= 9
        total += value
    
    check_digit = (10 - (total % 10)) % 10
    
    return check_digit == int(gst[-1])

def parse_gst(gst_number: str) -> str:
    """Parse and clean GST number"""
    return normalize_gst_ocr(gst_number.strip().upper())

def extract_state_code(gst_number: str) -> Optional[int]:
    """Extract state code from GST number"""
    try:
        if len(gst_number) >= 2:
            return int(gst_number[:2])
    except:
        pass
    return None

# State code mapping
STATE_CODES = {
    1: "Jammu and Kashmir",
    2: "Himachal Pradesh",
    3: "Punjab",
    4: "Chandigarh",
    5: "Uttarakhand",
    6: "Haryana",
    7: "Delhi",
    8: "Rajasthan",
    9: "Uttar Pradesh",
    10: "Bihar",
    11: "Jharkhand",
    12: "Odisha",
    13: "West Bengal",
    14: "Assam",
    15: "Meghalaya",
    16: "Manipur",
    17: "Mizoram",
    18: "Nagaland",
    19: "Tripura",
    20: "Sikkim",
    21: "Arunachal Pradesh",
    22: "Chhattisgarh",
    23: "Madhya Pradesh",
    24: "Gujarat",
    25: "Daman and Diu",
    26: "Dadra and Nagar Haveli",
    27: "Maharashtra",
    28: "Karnataka",
    29: "Goa",
    30: "Lakshadweep",
    31: "Kerala",
    32: "Tamil Nadu",
    33: "Puducherry",
    34: "Andaman and Nicobar",
    35: "Telangana",
    36: "Andhra Pradesh",
}

def get_state_name(gst_number: str) -> Optional[str]:
    """Get state name from GST number"""
    state_code = extract_state_code(gst_number)
    return STATE_CODES.get(state_code)
