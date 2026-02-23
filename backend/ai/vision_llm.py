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
        line_items = self._extract_line_items(lines)
        pan_candidates = self._extract_pan_candidates(lines, normalized)

        invoice_number, invoice_date_from_line = self._find_invoice_number_and_date(lines)
        invoice_date = invoice_date_from_line or self._find_invoice_date(lines)
        due_date = self._find_labeled_date(lines, ["due date", "payment due", "pay by", "terms"], avoid=["ack", "irn"])

        gst_numbers = self._extract_gst_candidates(normalized)

        buyer_block = self._extract_buyer_block(lines)
        vendor_block = self._extract_vendor_block(lines)

        vendor_name, vendor_address = self._parse_name_and_address(vendor_block)
        buyer_name, buyer_address = self._parse_name_and_address(buyer_block)

        vendor_name = self._extract_vendor_name_from_invoice_line(lines) or vendor_name

        vendor_gst = self._find_gst_in_lines(vendor_block)
        buyer_gst = self._find_gst_in_lines(buyer_block)

        if not vendor_gst and gst_numbers:
            if len(gst_numbers) > 1:
                vendor_gst = gst_numbers[0]
            elif not buyer_gst:
                vendor_gst = gst_numbers[0]
        if not buyer_gst and gst_numbers:
            if len(gst_numbers) > 1:
                buyer_gst = gst_numbers[-1]
            elif not vendor_gst:
                buyer_gst = gst_numbers[0]

        vendor_gst = self._repair_gst_with_pan(vendor_gst, pan_candidates)
        buyer_gst = self._repair_gst_with_pan(buyer_gst, pan_candidates)

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

        # If subtotal missing and line items are present, use line item totals.
        if invoice_amount is None and line_items:
            line_item_total = sum(item.get("total", 0.0) for item in line_items)
            if line_item_total > 0:
                invoice_amount = round(line_item_total, 2)

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

        # If tax still missing, infer from total and subtotal when possible.
        if tax_amount is None and total_amount is not None and invoice_amount is not None:
            inferred_tax = total_amount - invoice_amount
            if inferred_tax >= 0:
                tax_amount = round(inferred_tax, 2)

        if tax_rate is None:
            tax_rate = self._find_dominant_percentage(lines)

        currency = "INR" if ("\u20B9" in normalized or "inr" in lower_text or "rs" in lower_text) else None

        account_number = self._extract_account_number(lines)
        ifsc = self._extract_ifsc(lines)

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
        branch = self._extract_branch(lines)

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
            "line_items": line_items,
            "bank_details": {
                "account_number": account_number,
                "account_holder": account_holder,
                "bank_name": bank_name,
                "ifsc": ifsc,
                "branch": branch
            },
            "notes": None
        }

    def _normalize_text(self, text: str) -> str:
        text = text.replace("GST!N", "GSTIN").replace("GST1N", "GSTIN").replace("GSTIN/UIN", "GSTIN")
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        text = text.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
        text = re.sub(r"[|]+", " | ", text)
        # Fix common OCR errors for digits
        text = re.sub(r"(?<=\d)[Oo](?=\d)", "0", text)
        text = re.sub(r"\bO(?=\d)", "0", text)
        # Preserve line breaks; collapse only repeated spaces/tabs.
        text = re.sub(r"[ \t]{2,}", " ", text)
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
            line = self._clean_text_line(line)
            if not line:
                continue
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

    def _clean_text_line(self, line: str) -> str:
        cleaned = re.sub(r"^[^A-Za-z0-9]+", "", line)
        cleaned = cleaned.strip(" -:;,.|")
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned

    def _is_probable_name(self, line: str) -> bool:
        if len(line) < 3:
            return False
        if not re.search(r"[A-Za-z]{2,}", line):
            return False
        if re.search(r"\d{4,}", line):
            return False
        lowered = line.lower()
        noise = [
            "invoice", "tax", "original", "e-invoice", "irn", "ack", "date",
            "gst", "state", "code", "contact", "phone", "email", "bank",
            "amount", "total", "hsn", "sac", "qty", "rate", "delivery", "terms",
            "declaration", "dispatch", "reference", "market", "near", "road", "street",
            "gate", "nagar", "branch", "code", "lucknow", "firozabad", "pradesh"
        ]
        if any(n in lowered for n in noise):
            return False
        words = re.findall(r"[A-Za-z&.]+", line)
        if len(words) > 10:
            return False
        return True

    def _is_noise_line(self, line: str) -> bool:
        lowered = line.lower()
        return any(
            kw in lowered for kw in ["tax invoice", "e-invoice", "ack", "irn"]
        )

    def _is_stop_line(self, line: str) -> bool:
        lowered = line.lower()
        stop = [
            "gst", "gstin", "state", "code", "contact", "phone", "email", "pan", "invoice", "date",
            "delivery note", "mode/terms", "buyer", "consignee", "total", "bank details", "declaration"
        ]
        return any(s in lowered for s in stop)

    def _extract_vendor_name_from_invoice_line(self, lines: List[str]) -> Optional[str]:
        for line in lines:
            lower = line.lower()
            if "invoice" in lower and ("no" in lower or "number" in lower):
                prefix = re.split(r"invoice", line, flags=re.IGNORECASE)[0]
                if "," in prefix:
                    prefix = prefix.split(",")[-1]
                candidate = self._clean_text_line(prefix)
                if self._is_probable_name(candidate):
                    return candidate
        return None

    def _find_invoice_number_and_date(self, lines: List[str]) -> Tuple[Optional[str], Optional[str]]:
        best_number = None
        best_number_score = -1
        best_date = None

        for i, line in enumerate(lines):
            lower = line.lower()
            if "invoice" not in lower:
                continue
            if not any(token in lower for token in ["no", "number", "inv", "#", "dated"]):
                continue
            if "tax invoice" in lower and ("no" not in lower and "number" not in lower):
                continue

            candidate_lines = [line]
            if i + 1 < len(lines):
                candidate_lines.append(lines[i + 1])
            if i + 2 < len(lines):
                candidate_lines.append(lines[i + 2])

            for candidate_line in candidate_lines:
                number = self._extract_invoice_number(candidate_line)
                if number:
                    score = self._invoice_number_score(number)
                    if score > best_number_score:
                        best_number = number
                        best_number_score = score

                if best_date is None:
                    best_date = self._extract_date_from_line(candidate_line)

        return best_number, best_date

    def _invoice_number_score(self, value: str) -> int:
        token = value.strip().upper()
        score = 0
        if any(char.isalpha() for char in token):
            score += 3
        if any(char.isdigit() for char in token):
            score += 3
        if "/" in token or "-" in token:
            score += 2
        if 5 <= len(token) <= 24:
            score += 1
        if parse_date(token):
            score -= 4
        if token.isdigit():
            score -= 3
        if token.startswith(("IRN", "ACK", "GST", "PAN", "HSN")):
            score -= 5
        return score

    def _extract_invoice_number(self, line: str) -> Optional[str]:
        if not line:
            return None
        lowered = line.lower()
        if "irn" in lowered or "ack no" in lowered:
            return None

        matches = re.findall(r"\b[A-Z0-9][A-Z0-9\-/]{2,30}\b", line, re.IGNORECASE)
        best = None
        best_score = -1
        for match in matches:
            token = match.strip().strip(".,:;|")
            if not re.search(r"\d", token):
                continue
            if parse_date(token):
                continue
            if token.upper() in {"IRN", "ACK", "NO", "DATED", "INVOICE"}:
                continue
            score = self._invoice_number_score(token)
            if score > best_score:
                best = token
                best_score = score
        return best

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
            if any(skip in lower for skip in ["ack", "irn", "contact", "phone", "pan", "gstin/uin"]):
                continue
            if any(label in lower for label in labels):
                values = self._extract_decimal_amounts(line)
                if not values:
                    for match in re.finditer(REGEX_PATTERNS["amount"], line):
                        value = parse_amount(match.group(0))
                        if value is not None:
                            values.append(value)
                for value in values:
                    if value is not None and value < 1_000_000_000:
                        candidates.append(value)
        return max(candidates) if candidates else None

    def _find_total_amount(self, lines: List[str]) -> Optional[float]:
        # Prioritize explicit totals
        candidates = []
        for line in lines:
            lower = line.lower()
            if not any(label in lower for label in ["grand total", "amount due", "total amount", "total"]):
                continue
            if any(skip in lower for skip in ["tax amount (in words)", "hsn/sac", "taxable", "cgst", "sgst", "igst"]):
                continue
            values = self._extract_decimal_amounts(line)
            if values:
                candidates.extend(values)
        if candidates:
            return max(candidates)
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
            matches = self._extract_gst_candidates(line)
            if matches:
                return matches[0]
        return None

    def _find_all_regex(self, text: str, pattern: str) -> List[str]:
        try:
            return re.findall(pattern, text, re.IGNORECASE)
        except Exception:
            return []

    def _extract_decimal_amounts(self, line: str) -> List[float]:
        matches = re.findall(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})", line)
        values = []
        for match in matches:
            value = parse_amount(match)
            if value is not None:
                values.append(value)
        return values

    def _find_dominant_percentage(self, lines: List[str]) -> Optional[float]:
        percentages = []
        for line in lines:
            for token in re.findall(r"(\d{1,2}(?:\.\d{1,2})?)\s*%", line):
                try:
                    value = float(token)
                except ValueError:
                    continue
                if 0 < value <= 50:
                    percentages.append(value)
        if not percentages:
            return None

        # Prefer the most frequent tax rate.
        frequency: Dict[float, int] = {}
        for value in percentages:
            frequency[value] = frequency.get(value, 0) + 1
        return max(frequency.items(), key=lambda item: item[1])[0]

    def _extract_gst_candidates(self, text: str) -> List[str]:
        results = []

        # Direct regex first.
        for match in self._find_all_regex(text, REGEX_PATTERNS["gst"]):
            if isinstance(match, tuple):
                match = "".join(match)
            candidate = normalize_gst_ocr(str(match).upper().strip())
            if candidate and candidate not in results:
                results.append(candidate)

        # OCR-tolerant fallback over compacted alphanumeric stream.
        compact = re.sub(r"[^A-Z0-9OIL]", "", text.upper())
        if len(compact) >= 15:
            # Looser OCR fallback pattern: allows alphanumerics in PAN-related slots.
            window_pattern = re.compile(
                r"^[0-9OIL]{2}[A-Z0-9OIL]{5}[0-9OIL]{4}[A-Z0-9OIL]{1}[A-Z0-9OIL]{1}Z[A-Z0-9OIL]{1}$"
            )
            for idx in range(len(compact) - 14):
                window = compact[idx:idx + 15]
                if window_pattern.match(window):
                    normalized = normalize_gst_ocr(window)
                    if normalized not in results:
                        results.append(normalized)

        return results

    def _extract_pan_candidates(self, lines: List[str], full_text: str) -> List[str]:
        results: List[str] = []

        for line in lines:
            if "pan" not in line.lower():
                continue
            for match in re.findall(REGEX_PATTERNS["pan"], line, re.IGNORECASE):
                candidate = str(match).upper()
                if candidate not in results:
                    results.append(candidate)

        if results:
            return results

        for match in re.findall(REGEX_PATTERNS["pan"], full_text, re.IGNORECASE):
            candidate = str(match).upper()
            if candidate not in results:
                results.append(candidate)

        return results

    def _repair_gst_with_pan(self, gst_value: Optional[str], pan_candidates: List[str]) -> Optional[str]:
        if not gst_value:
            return gst_value

        gst = re.sub(r"[^A-Z0-9]", "", str(gst_value).upper())
        if len(gst) != 15:
            return gst_value

        if not pan_candidates:
            return gst

        for pan in pan_candidates:
            mismatch = sum(1 for a, b in zip(gst[2:12], pan) if a != b)
            has_digit_in_alpha_slot = any(char.isdigit() for char in gst[2:7])
            if mismatch <= 2 or has_digit_in_alpha_slot:
                return f"{gst[:2]}{pan}{gst[12:]}"

        return gst

    def _extract_account_number(self, lines: List[str]) -> Optional[str]:
        labeled_values: List[str] = []
        generic_values: List[str] = []

        for line in lines:
            normalized_line = line.replace("O", "0").replace("o", "0")
            candidates = re.findall(r"\b\d{9,18}\b", normalized_line)
            if not candidates:
                continue

            lower = line.lower()
            if any(label in lower for label in ["a/c", "account", "bank"]):
                labeled_values.extend(candidates)
            else:
                generic_values.extend(candidates)

        source = labeled_values or generic_values
        if not source:
            return None

        # Prefer the longest number, usually the account number.
        source.sort(key=len, reverse=True)
        return source[0]

    def _extract_ifsc(self, lines: List[str]) -> Optional[str]:
        def normalize_ifsc(candidate: str) -> Optional[str]:
            value = re.sub(r"[^A-Z0-9]", "", candidate.upper())
            if len(value) < 11:
                return None
            value = value[:11]
            value = value[:4] + "0" + value[5:]
            if re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", value):
                return value
            return None

        patterns = [
            REGEX_PATTERNS["ifsc"],
            r"[A-Z]{4}[0O][A-Z0-9O]{6}",
        ]

        for line in lines:
            lower = line.lower()
            if not any(label in lower for label in ["ifsc", "ifs code", "branch"]):
                continue
            for pattern in patterns:
                for match in re.findall(pattern, line, re.IGNORECASE):
                    normalized = normalize_ifsc(str(match))
                    if normalized:
                        return normalized
        return None

    def _extract_branch(self, lines: List[str]) -> Optional[str]:
        for line in lines:
            lower = line.lower()
            if "branch" not in lower:
                continue
            if ":" in line:
                value = line.split(":", 1)[1].strip()
                if "&" in value:
                    value = value.split("&", 1)[0].strip()
                cleaned = self._clean_text_line(value)
                return cleaned if cleaned else None
        return None

    def _extract_line_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for line in lines:
            compact = re.sub(r"\s+", " ", line).strip()
            if not compact:
                continue
            if "description" in compact.lower() or "hsn/sac" in compact.lower():
                continue
            if "total" in compact.lower() and not re.match(r"^\d+\s+", compact):
                continue
            if not re.match(r"^\d+\s+", compact):
                continue

            tokens = compact.split()
            if len(tokens) < 7:
                continue

            hsn_idx = -1
            for idx in range(1, len(tokens)):
                if re.match(r"^\d{4,8}$", tokens[idx]):
                    hsn_idx = idx
                    break
            if hsn_idx <= 1:
                continue

            description = " ".join(tokens[1:hsn_idx]).strip(" -:,.;")
            if not description:
                continue

            remainder = tokens[hsn_idx + 1:]
            qty = None
            qty_idx = None
            for idx, token in enumerate(remainder):
                if re.match(r"^\d+(?:\.\d+)?$", token):
                    qty = parse_amount(token)
                    qty_idx = idx
                    break
            if qty is None or qty_idx is None:
                continue

            unit = ""
            if qty_idx + 1 < len(remainder):
                unit_candidate = remainder[qty_idx + 1].strip(".,;:|")
                if re.match(r"^[A-Za-z]{1,6}$", unit_candidate):
                    unit = unit_candidate

            start_idx = qty_idx + 2 if unit else qty_idx + 1
            trailing_text = " ".join(remainder[start_idx:])
            monetary_values = self._extract_decimal_amounts(trailing_text)
            if not monetary_values:
                continue

            unit_price = monetary_values[0]
            total = monetary_values[-1] if len(monetary_values) > 1 else round(unit_price * qty, 2)

            items.append(
                {
                    "description": description,
                    "quantity": qty,
                    "unit": unit or "Nos",
                    "unit_price": unit_price,
                    "total": total,
                }
            )

        return items
