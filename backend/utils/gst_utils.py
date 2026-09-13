import re
from typing import Optional
from backend.utils.regex_utils import GSTIN_PATTERN


def validate_gstin(gstin: Optional[str]) -> bool:
    if not gstin or not isinstance(gstin, str):
        return False
    cleaned = gstin.strip().upper()
    return bool(re.match(r"^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z0-9]{1}Z[A-Z0-9]{1}$", cleaned))


def normalize_gstin(gstin: Optional[str]) -> Optional[str]:
    if not gstin or not isinstance(gstin, str):
        return None
    cleaned = re.sub(r"[^A-Z0-9]", "", gstin.upper())
    if len(cleaned) == 15 and validate_gstin(cleaned):
        return cleaned
    match = re.search(GSTIN_PATTERN, gstin.upper())
    if match:
        return match.group(0)
    return cleaned if len(cleaned) == 15 else None
