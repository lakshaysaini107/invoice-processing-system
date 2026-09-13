import re
from typing import Optional


def parse_amount(val: Optional[str]) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    text = str(val).strip()
    if not text:
        return None
    cleaned = re.sub(r"[^\d.-]", "", text.replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return None


def calculate_tax_from_total(total_amount: float, tax_rate: float) -> float:
    if tax_rate <= 0:
        return 0.0
    return round(total_amount - (total_amount / (1 + (tax_rate / 100))), 2)
