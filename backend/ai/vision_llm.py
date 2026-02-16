import re
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from backend.core.logging import logger
from backend.utils.regex_utils import REGEX_PATTERNS
from backend.utils.date_utils import parse_date
from backend.utils.math_utils import parse_amount
from backend.utils.gst_utils import normalize_gst_ocr

class VisionLLMEngine:
    """
    Extract structured invoice fields using simple heuristics.
    This version does NOT require any API keys or external LLM services.
    """

    def __init__(self):
        pass

    async def extract_fields(
        self,
        image: np.ndarray,
        ocr_text: str,
        layout_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Heuristic extraction using OCR text and basic regex rules.
        """
        try:
            extracted_fields = self._extract_from_text(ocr_text or "")
            logger.info("Heuristic extraction completed")
            return extracted_fields

        except Exception as e:
            logger.error(f"Heuristic extraction error: {str(e)}")
            raise

    def _extract_from_text(self, text: str) -> Dict[str, Any]:
        """Extract basic fields from OCR text using regex heuristics."""
        normalized = self._normalize_text(text)
        lines = self._split_lines(normalized)
        lower_text = normalized.lower()

        invoice_number, invoice_date_from_line = self._find_invoice_number_and_date(lines)
        invoice_date = invoice_date_from_line or self._find_invoice_date(lines)
        due_date = self._find_labeled_date(lines, ["due date", "payment due", "pay by", "terms"], avoid=["ack", "irn"])

        gst_numbers = [normalize_gst_ocr(g) for g in self._find_all_regex(normalized, REGEX_PATTERNS["gst"])]

        buyer_block = self._extract_buyer_block(lines)
        vendor_block = self._extract_vendor_block(lines)

        vendor_name, vendor_address = self._parse_name_and_address(vendor_block)
        buyer_name, buyer_address = self._parse_name_and_address(buyer_block)

        vendor_name = self._extract_vendor_name_from_invoice_line(lines) or vendor_name

        vendor_gst = self._find_gst_in_lines(vendor_block)
        buyer_gst = self._find_gst_in_lines(buyer_block)

        if not vendor_gst and gst_numbers:
            vendor_gst = gst_numbers[0]
        if not buyer_gst and len(gst_numbers) > 1:
            buyer_gst = gst_numbers[1]

        purchase_order_number = self._find_labeled_code(
            lines,
            label_patterns=[r"po\s*no", r"purchase\s*order", r"order\s*no"],
        )

        tax_rate = self._find_percentage(lines, labels=["tax rate", "gst", "cgst", "sgst", "igst"])            or self._find_percentage(lines, labels=["tax %", "gst %"])

        tax_amount = self._sum_tax_amounts(lines)
        if tax_amount is None:
            tax_amount = self._find_amount(lines, ["tax", "gst", "vat", "cgst", "sgst", "igst"])

        invoice_amount = self._find_amount(
            lines,
            ["subtotal", "sub total", "amount before tax", "taxable", "taxable value", "amount chargeable"]
        )

        total_amount = self._find_total_amount(lines)

        # If subtotal missing, infer from total - tax
        if invoice_amount is None and total_amount is not None and tax_amount is not None:
            inferred = total_amount - tax_amount
            if inferred > 0:
                invoice_amount = round(inferred, 2)

        # If total still missing, pick the largest amount as total
        if total_amount is None:
            amounts = [parse_amount(a) for a in self._find_all_regex(normalized, REGEX_PATTERNS["amount"]) ]
            amounts = [a for a in amounts if a is not None]
            total_amount = max(amounts) if amounts else None

        # If subtotal missing but total exists, pick largest amount below total
        if invoice_amount is None and total_amount is not None:
            amounts = [parse_amount(a) for a in self._find_all_regex(normalized, REGEX_PATTERNS["amount"]) ]
            amounts = [a for a in amounts if a is not None and a < total_amount]
            invoice_amount = max(amounts) if amounts else None

        currency = "INR" if ("\u20B9" in normalized or "inr" in lower_text or "rs" in lower_text) else None

        account_number_match = self._find_labeled_regex(
            lines,
            label_patterns=[r"a/c\s*no", r"account\s*no"],
            value_pattern=REGEX_PATTERNS["account_number"],
        )
        account_numbers = self._find_all_regex(normalized, REGEX_PATTERNS["account_number"])
        account_number = account_number_match or (account_numbers[0] if account_numbers else None)

        ifsc_match = self._find_labeled_regex(
            lines,
            label_patterns=[r"ifsc"],
            value_pattern=REGEX_PATTERNS["ifsc"],
        )
        ifsc_matches = self._find_all_regex(normalized, REGEX_PATTERNS["ifsc"])
        ifsc = ifsc_match or (ifsc_matches[0] if ifsc_matches else None)

        account_holder = self._find_value_after_label(
            lines,
            label_patterns=[r"a/c\s*holder", r"account\s*holder"],
        )
        bank_name = self._find_value_after_label(
            lines,
            label_patterns=[r"bank\s*name"],
        )
        if bank_name and "a/c" in bank_name.lower():
            bank_name = bank_name.split("a/c", 1)[0].strip()

        payment_terms = self._find_value_after_label(
            lines,
            label_patterns=[r"payment\s*terms", r"terms\s*of\s*payment"],
        )

        return {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "due_date": due_date,
            "vendor_name": vendor_name,
            "vendor_gst": vendor_gst,
            "vendor_address": vendor_address,
            "buyer_name": buyer_name,
            "buyer_gst": buyer_gst,
            "buyer_address": buyer_address,
            "invoice_amount": invoice_amount,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "tax_rate": tax_rate,
            "currency": currency,
            "payment_terms": payment_terms,
            "purchase_order_number": purchase_order_number,
            "line_items": [],
            "bank_details": {
                "account_number": account_number,
                "account_holder": account_holder,
                "bank_name": bank_name,
                "ifsc": ifsc,
                "branch": None
            },
            "notes": None
        }

    def _normalize_text(self, text: str) -> str:
        text = text.replace("GST!N", "GSTIN").replace("GST1N", "GSTIN")
        text = text.replace("GSTIN/UIN", "GSTIN")
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        # Fix common OCR errors for digits
        text = re.sub(r"(?<=\d)[Oo](?=\d)", "0", text)
        text = re.sub(r"\bO(?=\d)", "0", text)
        return text

    def _split_lines(self, text: str) -> List[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]

    def _extract_buyer_block(self, lines: List[str]) -> List[str]:
        # Prefer explicit "Buyer (Bill to)" blocks
        for idx, line in enumerate(lines):
            lower = line.lower()
            if "buyer" in lower and "bill" in lower:
                return self._collect_block(lines, idx + 1)

        # Fallback to consignee/ship-to blocks
        for idx, line in enumerate(lines):
            lower = line.lower()
            if ("consignee" in lower or "ship to" in lower or "bill to" in lower or "customer" in lower):
                if "order" in lower:
                    continue
                return self._collect_block(lines, idx + 1)

        return []

    def _extract_vendor_block(self, lines: List[str]) -> List[str]:
        # If invoice line exists, start from there
        for idx, line in enumerate(lines):
            lower = line.lower()
            if "invoice" in lower and ("no" in lower or "number" in lower) and "tax invoice" not in lower:
                return self._collect_block(lines, idx, end_labels=["consignee", "buyer", "bill to", "ship to", "customer"], max_lines=10)

        # Vendor/seller keywords
        for idx, line in enumerate(lines):
            lower = line.lower()
            if any(label in lower for label in ["seller", "supplier", "vendor", "from", "billed by", "party"]):
                return self._collect_block(lines, idx + 1, end_labels=["consignee", "buyer", "bill to", "ship to", "customer"], max_lines=10)

        # Fallback to header
        return self._collect_block(lines, 0, end_labels=["consignee", "buyer", "bill to", "ship to", "customer"], max_lines=10)

    def _collect_block(
        self,
        lines: List[str],
        start_idx: int,
        end_labels: Optional[List[str]] = None,
        max_lines: int = 8
    ) -> List[str]:
        end_labels = end_labels or []
        block = []
        for line in lines[start_idx:start_idx + max_lines]:
            lower = line.lower()
            if any(label in lower for label in end_labels):
                break
            if not line.strip():
                if block:
                    break
                continue
            block.append(line)
        return block

    def _parse_name_and_address(self, lines: List[str]) -> Tuple[Optional[str], Optional[str]]:
        if not lines:
            return None, None

        name = None
        address_lines = []

        for line in lines:
            if self._is_noise_line(line):
                continue

            if name is None and self._is_probable_name(line):
                name = line
                continue

            if name:
                if self._is_stop_line(line):
                    break
                address_lines.append(line)

        address = ", ".join(address_lines) if address_lines else None
        return name, address

    def _is_probable_name(self, line: str) -> bool:
        if len(line) < 3:
            return False
        if not re.search(r"[A-Za-z]{2,}", line):
            return False
        lowered = line.lower()
        noise = [
            "invoice", "tax", "original", "e-invoice", "irn", "ack", "date",
            "gst", "state", "code", "contact", "phone", "email", "bank",
            "amount", "total", "hsn", "sac", "qty", "rate"
        ]
        if any(n in lowered for n in noise):
            return False
        return True

    def _is_noise_line(self, line: str) -> bool:
        lowered = line.lower()
        return any(
            kw in lowered for kw in ["invoice", "tax invoice", "e-invoice", "ack", "irn"]
        )

    def _is_stop_line(self, line: str) -> bool:
        lowered = line.lower()
        stop = ["gst", "gstin", "state", "code", "contact", "phone", "email", "pan", "invoice", "date"]
        return any(s in lowered for s in stop)

    def _extract_vendor_name_from_invoice_line(self, lines: List[str]) -> Optional[str]:
        for line in lines:
            lower = line.lower()
            if "invoice" in lower and ("no" in lower or "number" in lower):
                prefix = re.split(r"invoice", line, flags=re.IGNORECASE)[0]
                if "," in prefix:
                    prefix = prefix.split(",")[-1]
                candidate = prefix.strip(" -:.<>")
                if self._is_probable_name(candidate):
                    return candidate
        return None

    def _find_invoice_number_and_date(self, lines: List[str]) -> Tuple[Optional[str], Optional[str]]:
        for i, line in enumerate(lines):
            lower = line.lower()
            if "invoice" in lower and ("no" in lower or "number" in lower or "inv" in lower or "#" in lower):
                number = self._extract_invoice_number(line)
                date = self._extract_date_from_line(line)
                if not number and i + 1 < len(lines):
                    number = self._extract_invoice_number(lines[i + 1])
                if not date and i + 1 < len(lines):
                    date = self._extract_date_from_line(lines[i + 1])
                return number, date
        return None, None

    def _extract_invoice_number(self, line: str) -> Optional[str]:
        matches = re.findall(r"\b[A-Z0-9][A-Z0-9\-/]{2,30}\b", line, re.IGNORECASE)
        for match in matches:
            if re.search(r"\d", match):
                return match.strip()
        return None

    def _find_invoice_date(self, lines: List[str]) -> Optional[str]:
        # Prefer lines that mention invoice and date together
        for i, line in enumerate(lines):
            lower = line.lower()
            if "invoice" in lower and ("date" in lower or "dated" in lower):
                date = self._extract_date_from_line(line)
                if not date and i + 1 < len(lines):
                    date = self._extract_date_from_line(lines[i + 1])
                if date:
                    return date

        # Fallback: first date that isn't an ACK/IRN date
        for line in lines:
            lower = line.lower()
            if "ack" in lower or "irn" in lower:
                continue
            date = self._extract_date_from_line(line)
            if date:
                return date

        return None

    def _find_labeled_date(self, lines: List[str], labels: List[str], avoid: Optional[List[str]] = None) -> Optional[str]:
        avoid = avoid or []
        for line in lines:
            lower = line.lower()
            if any(a in lower for a in avoid):
                continue
            if any(label in lower for label in labels):
                date = self._extract_date_from_line(line)
                if date:
                    return date
        return None

    def _extract_date_from_line(self, line: str) -> Optional[str]:
        matches = re.findall(REGEX_PATTERNS["date"], line)
        for match in matches:
            parsed = parse_date(match)
            if parsed:
                return parsed
        return None

    def _find_labeled_value(
        self,
        lines: List[str],
        label_patterns: List[str],
        value_pattern: str
    ) -> Optional[str]:
        for line in lines:
            line_lower = line.lower()
            for label in label_patterns:
                if re.search(label, line_lower):
                    match = re.search(value_pattern, line, re.IGNORECASE)
                    if match:
                        return match.group(0).strip()
        return None

    def _find_value_after_label(self, lines: List[str], label_patterns: List[str]) -> Optional[str]:
        for line in lines:
            lower = line.lower()
            if any(re.search(label, lower) for label in label_patterns):
                if ":" in line:
                    value = line.split(":", 1)[1].strip()
                    return value if value else None
        return None

    def _find_labeled_regex(
        self,
        lines: List[str],
        label_patterns: List[str],
        value_pattern: str
    ) -> Optional[str]:
        for line in lines:
            lower = line.lower()
            if any(re.search(label, lower) for label in label_patterns):
                match = re.search(value_pattern, line)
                if match:
                    return match.group(0).strip()
        return None

    def _find_labeled_code(self, lines: List[str], label_patterns: List[str]) -> Optional[str]:
        for line in lines:
            lower = line.lower()
            if any(re.search(label, lower) for label in label_patterns):
                matches = re.findall(r"\b[A-Z0-9][A-Z0-9\-/]{2,30}\b", line, re.IGNORECASE)
                for match in matches:
                    if re.search(r"\d", match):
                        return match.strip()
        return None

    def _find_amount(self, lines: List[str], labels: List[str]) -> Optional[float]:
        candidates = []
        for line in lines:
            lower = line.lower()
            if any(label in lower for label in labels):
                for match in re.finditer(REGEX_PATTERNS["amount"], line):
                    value = parse_amount(match.group(0))
                    if value is not None:
                        candidates.append(value)
        return max(candidates) if candidates else None

    def _find_total_amount(self, lines: List[str]) -> Optional[float]:
        # Prioritize explicit totals
        priority_labels = [
            ["grand total", "amount due", "total amount"],
            ["total"],
        ]
        for labels in priority_labels:
            amount = self._find_amount(lines, labels)
            if amount is not None:
                return amount
        return None

    def _sum_tax_amounts(self, lines: List[str]) -> Optional[float]:
        cgst = self._find_amount(lines, ["cgst"])
        sgst = self._find_amount(lines, ["sgst"])
        igst = self._find_amount(lines, ["igst"])

        if cgst is not None and sgst is not None:
            return round(cgst + sgst, 2)
        if igst is not None:
            return igst
        return None

    def _find_percentage(self, lines: List[str], labels: List[str]) -> Optional[float]:
        for line in lines:
            lower = line.lower()
            if any(label in lower for label in labels):
                match = re.search(r"(\d{1,2}(?:\.\d{1,2})?)\s*%", line)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        continue
        return None

    def _find_gst_in_lines(self, lines: List[str]) -> Optional[str]:
        for line in lines:
            matches = self._find_all_regex(line, REGEX_PATTERNS["gst"])
            if matches:
                return normalize_gst_ocr(matches[0])
        return None

    def _find_all_regex(self, text: str, pattern: str) -> List[str]:
        try:
            return re.findall(pattern, text, re.IGNORECASE)
        except Exception:
            return []
