from typing import Optional, Union
import re

def parse_amount(value: Union[str, int, float]) -> Optional[float]:
    """Parse amount from various formats and return float"""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None

        # Remove currency words
        cleaned = re.sub(r"(?i)\b(inr|usd|eur|rs\.?)\b", "", cleaned)

        # Remove any remaining non-numeric symbols (keep digits, dot, comma, minus, parentheses)
        cleaned = re.sub(r"[^0-9.,()\-]", "", cleaned)

        # Handle negatives written in parentheses
        negative = False
        if cleaned.startswith("(") and cleaned.endswith(")"):
            negative = True
            cleaned = cleaned[1:-1]

        # Remove spaces and thousands separators
        cleaned = cleaned.replace(" ", "").replace(",", "")

        # Trim trailing punctuation
        cleaned = cleaned.strip("=,:;")

        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
        if not match:
            return None

        try:
            value = float(match.group(0))
            return -value if negative else value
        except ValueError:
            return None

    return None

def validate_amount(value: Union[str, float]) -> bool:
    """Check if value is a valid amount"""
    parsed = parse_amount(value)
    return parsed is not None and parsed > 0

def calculate_tax(amount: float, tax_rate: float) -> float:
    """Calculate tax amount"""
    return round(amount * (tax_rate / 100), 2)

def calculate_total(subtotal: float, tax: float) -> float:
    """Calculate total amount"""
    return round(subtotal + tax, 2)

def validate_invoice_math(subtotal: float, tax: float, total: float) -> bool:
    """Validate if invoice amounts match"""
    calculated_total = calculate_total(subtotal, tax)
    return abs(calculated_total - total) < 0.01  # Allow for rounding errors

def extract_amounts_from_text(text: str) -> list:
    """Extract all amounts from text"""
    amounts = []

    # Pattern for amounts with currency symbols
    pattern = r"(?:Rs\.?|INR|\u20B9|\$|USD|EUR|\u20AC)?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)"
    matches = re.findall(pattern, text, re.IGNORECASE)

    for match in matches:
        parsed = parse_amount(match)
        if parsed is not None:
            amounts.append(parsed)

    return amounts

def format_amount(value: float, currency: str = "INR") -> str:
    """Format amount with currency"""
    if currency == "INR":
        return f"\u20B9{value:,.2f}"
    if currency == "USD":
        return f"${value:,.2f}"
    if currency == "EUR":
        return f"\u20AC{value:,.2f}"
    return f"{value:,.2f}"
