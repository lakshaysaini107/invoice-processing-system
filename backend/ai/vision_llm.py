import re
from typing import Any, Dict, List, Optional
from backend.utils.date_utils import parse_date
from backend.utils.gst_utils import normalize_gstin
from backend.utils.math_utils import parse_amount
from backend.utils.regex_utils import (
    ACCOUNT_NO_PATTERN,
    AMOUNT_PATTERN,
    GSTIN_PATTERN,
    IFSC_PATTERN,
    INVOICE_NO_PATTERNS,
    PO_PATTERNS,
)


class HeuristicInvoiceExtractor:
    def extract_fields(self, ocr_data: Dict[str, Any]) -> Dict[str, Any]:
        full_text = ocr_data.get("full_text", "")
        lines = [l.strip() for l in full_text.split("\n") if l.strip()]

        result = {
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "vendor_name": None,
            "vendor_gst": None,
            "vendor_address": None,
            "buyer_name": None,
            "buyer_gst": None,
            "buyer_address": None,
            "invoice_amount": None,
            "tax_amount": None,
            "total_amount": None,
            "tax_rate": None,
            "currency": "INR",
            "payment_terms": None,
            "purchase_order_number": None,
            "notes": None,
            "bank_details": {
                "account_number": None,
                "account_holder": None,
                "bank_name": None,
                "ifsc": None,
                "branch": None,
            },
            "line_items": [],
        }

        # 1. GSTINs
        gstins = re.findall(GSTIN_PATTERN, full_text.upper())
        if gstins:
            result["vendor_gst"] = normalize_gstin(gstins[0])
            if len(gstins) > 1:
                result["buyer_gst"] = normalize_gstin(gstins[1])

        # 2. Invoice Number
        for pattern in INVOICE_NO_PATTERNS:
            match = re.search(pattern, full_text)
            if match:
                inv_no = match.group(1).strip(" :#,.-")
                if len(inv_no) >= 2:
                    result["invoice_number"] = inv_no
                    break

        # 3. PO Number
        for pattern in PO_PATTERNS:
            match = re.search(pattern, full_text)
            if match:
                result["purchase_order_number"] = match.group(1).strip(" :#,.-")
                break

        # 4. Dates
        dates = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", full_text)
        if dates:
            result["invoice_date"] = parse_date(dates[0])
            if len(dates) > 1:
                result["due_date"] = parse_date(dates[1])

        # 5. Amounts
        total_match = re.search(r"(?i)(?<!sub)(?:total\s*amount|grand\s*total|net\s*payable|amount\s*due|\btotal)[:\s]*[₹\s]*([0-9,]+(?:\.[0-9]{2})?)", full_text)
        if total_match:
            result["total_amount"] = parse_amount(total_match.group(1))

        subtotal_match = re.search(r"(?i)(?:subtotal|sub-total|taxable\s*value)[:\s]*[₹\s]*([0-9,]+(?:\.[0-9]{2})?)", full_text)
        if subtotal_match:
            result["invoice_amount"] = parse_amount(subtotal_match.group(1))

        tax_match = re.search(r"(?i)(?:tax|gst|cgst|sgst|igst|vat)\s*(?:amount|val)?[:\s]*[₹\s]*([0-9,]+(?:\.[0-9]{2})?)", full_text)
        if tax_match:
            result["tax_amount"] = parse_amount(tax_match.group(1))


        if result["total_amount"] and not result["invoice_amount"]:
            if result["tax_amount"]:
                result["invoice_amount"] = round(result["total_amount"] - result["tax_amount"], 2)
            else:
                result["invoice_amount"] = result["total_amount"]

        # 6. Vendor & Buyer Names heuristics
        if lines:
            result["vendor_name"] = lines[0][:100]
            for l in lines[1:5]:
                if any(kw in l.lower() for kw in ["pvt", "ltd", "inc", "corp", "company", "services", "enterprises"]):
                    result["vendor_name"] = l[:100]
                    break

        buyer_idx = -1
        for i, l in enumerate(lines):
            if any(kw in l.lower() for kw in ["bill to", "buyer", "customer", "ship to"]):
                buyer_idx = i
                break
        if buyer_idx != -1 and buyer_idx + 1 < len(lines):
            result["buyer_name"] = lines[buyer_idx + 1][:100]

        # 7. Bank Details
        ifsc_match = re.search(IFSC_PATTERN, full_text)
        if ifsc_match:
            result["bank_details"]["ifsc"] = ifsc_match.group(0)

        acc_match = re.search(r"(?i)(?:account|acc|a/c)\s*(?:no|number)?[:\s]*(\d{9,18})", full_text)
        if acc_match:
            result["bank_details"]["account_number"] = acc_match.group(1)

        bank_name_match = re.search(r"(?i)(?:bank\s*name|bank)[:\s]*([A-Za-z\s]+Bank)", full_text)
        if bank_name_match:
            result["bank_details"]["bank_name"] = bank_name_match.group(1).strip()

        # 8. Basic Line Items heuristic extraction
        line_items = []
        item_patterns = re.findall(r"([A-Za-z0-9\s]{3,40})\s+(\d+)\s+([0-9,]+(?:\.[0-9]{2})?)\s+([0-9,]+(?:\.[0-9]{2})?)", full_text)
        for item in item_patterns[:10]:
            desc, qty, price, amt = item
            if desc.strip().lower() not in ["subtotal", "total", "tax", "amount"]:
                line_items.append({
                    "description": desc.strip(),
                    "quantity": parse_amount(qty),
                    "unit_price": parse_amount(price),
                    "amount": parse_amount(amt),
                })
        result["line_items"] = line_items

        return result


vision_llm_extractor = HeuristicInvoiceExtractor()
