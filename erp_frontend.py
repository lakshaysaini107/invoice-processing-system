from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Tuple

import requests
import streamlit as st
from requests import RequestException


DEFAULT_BACKEND_API = os.getenv("ERP_BACKEND_API", "http://localhost:8001/api")


st.set_page_config(page_title="ERP Invoice Form", layout="wide")


def init_state() -> None:
    if "erp_backend_api" not in st.session_state:
        st.session_state.erp_backend_api = DEFAULT_BACKEND_API
    if "erp_loaded_source_invoice_id" not in st.session_state:
        st.session_state.erp_loaded_source_invoice_id = None
    if "erp_last_save_message" not in st.session_state:
        st.session_state.erp_last_save_message = None


def decode_response_json(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        text = response.text.strip()
        return {"detail": text or "Empty response"}


def get_json(url: str, timeout: float = 10.0) -> Tuple[Optional[Any], Optional[str]]:
    try:
        response = requests.get(url, timeout=timeout)
    except RequestException as exc:
        return None, str(exc)
    payload = decode_response_json(response)
    if response.ok:
        return payload, None
    return None, str(payload)


def post_json(url: str, payload: Dict[str, Any], timeout: float = 15.0) -> Tuple[Optional[Any], Optional[str]]:
    try:
        response = requests.post(url, json=payload, timeout=timeout)
    except RequestException as exc:
        return None, str(exc)
    decoded = decode_response_json(response)
    if response.ok:
        return decoded, None
    return None, str(decoded)


def blank_invoice() -> Dict[str, Any]:
    return {
        "source_invoice_id": None,
        "invoice_number": "",
        "invoice_date": "",
        "due_date": "",
        "vendor_name": "",
        "vendor_gst": "",
        "vendor_address": "",
        "buyer_name": "",
        "buyer_gst": "",
        "buyer_address": "",
        "invoice_amount": "",
        "tax_amount": "",
        "total_amount": "",
        "tax_rate": "",
        "currency": "",
        "payment_terms": "",
        "purchase_order_number": "",
        "notes": "",
        "bank_details": {
            "account_number": "",
            "account_holder": "",
            "bank_name": "",
            "ifsc": "",
            "branch": "",
        },
        "line_items": [],
    }


def normalize_invoice(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    invoice = blank_invoice()
    incoming = payload or {}
    for key in invoice.keys():
        if key == "bank_details":
            bank = incoming.get("bank_details")
            if isinstance(bank, dict):
                for bank_key in invoice["bank_details"].keys():
                    value = bank.get(bank_key)
                    invoice["bank_details"][bank_key] = "" if value is None else str(value)
            continue
        if key == "line_items":
            invoice["line_items"] = incoming.get("line_items") if isinstance(incoming.get("line_items"), list) else []
            continue
        value = incoming.get(key)
        invoice[key] = "" if value is None else str(value)
    return invoice


def load_current_invoice() -> None:
    payload, error = get_json(f"{st.session_state.erp_backend_api}/erp/get_current_invoice")
    if error:
        st.error(f"Could not load current invoice: {error}")
        return
    if not isinstance(payload, dict):
        st.error("Unexpected ERP handoff payload.")
        return

    invoice = normalize_invoice(payload)
    bank = invoice["bank_details"]
    st.session_state.erp_source_invoice_id = invoice.get("source_invoice_id")
    st.session_state.erp_invoice_number = invoice.get("invoice_number", "")
    st.session_state.erp_invoice_date = invoice.get("invoice_date", "")
    st.session_state.erp_due_date = invoice.get("due_date", "")
    st.session_state.erp_vendor_name = invoice.get("vendor_name", "")
    st.session_state.erp_vendor_gst = invoice.get("vendor_gst", "")
    st.session_state.erp_vendor_address = invoice.get("vendor_address", "")
    st.session_state.erp_buyer_name = invoice.get("buyer_name", "")
    st.session_state.erp_buyer_gst = invoice.get("buyer_gst", "")
    st.session_state.erp_buyer_address = invoice.get("buyer_address", "")
    st.session_state.erp_invoice_amount = invoice.get("invoice_amount", "")
    st.session_state.erp_tax_amount = invoice.get("tax_amount", "")
    st.session_state.erp_total_amount = invoice.get("total_amount", "")
    st.session_state.erp_tax_rate = invoice.get("tax_rate", "")
    st.session_state.erp_currency = invoice.get("currency", "")
    st.session_state.erp_payment_terms = invoice.get("payment_terms", "")
    st.session_state.erp_purchase_order_number = invoice.get("purchase_order_number", "")
    st.session_state.erp_notes = invoice.get("notes", "")
    st.session_state.erp_account_number = bank.get("account_number", "")
    st.session_state.erp_account_holder = bank.get("account_holder", "")
    st.session_state.erp_bank_name = bank.get("bank_name", "")
    st.session_state.erp_ifsc = bank.get("ifsc", "")
    st.session_state.erp_branch = bank.get("branch", "")
    st.session_state.erp_line_items = json.dumps(invoice.get("line_items", []), indent=2)
    st.session_state.erp_loaded_source_invoice_id = invoice.get("source_invoice_id")


def build_save_payload() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    try:
        line_items = json.loads(st.session_state.get("erp_line_items", "") or "[]")
    except json.JSONDecodeError as exc:
        return None, f"Line items JSON is invalid: {exc}"
    if not isinstance(line_items, list):
        return None, "Line items must be a JSON array."

    def as_number(value: str) -> Optional[float]:
        text = str(value).strip()
        if not text:
            return None
        try:
            return float(text.replace(",", ""))
        except ValueError:
            return None

    payload = {
        "invoice_number": st.session_state.get("erp_invoice_number") or None,
        "invoice_date": st.session_state.get("erp_invoice_date") or None,
        "due_date": st.session_state.get("erp_due_date") or None,
        "vendor_name": st.session_state.get("erp_vendor_name") or None,
        "vendor_gst": st.session_state.get("erp_vendor_gst") or None,
        "vendor_address": st.session_state.get("erp_vendor_address") or None,
        "buyer_name": st.session_state.get("erp_buyer_name") or None,
        "buyer_gst": st.session_state.get("erp_buyer_gst") or None,
        "buyer_address": st.session_state.get("erp_buyer_address") or None,
        "invoice_amount": as_number(st.session_state.get("erp_invoice_amount", "")),
        "tax_amount": as_number(st.session_state.get("erp_tax_amount", "")),
        "total_amount": as_number(st.session_state.get("erp_total_amount", "")),
        "tax_rate": as_number(st.session_state.get("erp_tax_rate", "")),
        "currency": st.session_state.get("erp_currency") or None,
        "payment_terms": st.session_state.get("erp_payment_terms") or None,
        "purchase_order_number": st.session_state.get("erp_purchase_order_number") or None,
        "notes": st.session_state.get("erp_notes") or None,
        "bank_details": {
            "account_number": st.session_state.get("erp_account_number") or None,
            "account_holder": st.session_state.get("erp_account_holder") or None,
            "bank_name": st.session_state.get("erp_bank_name") or None,
            "ifsc": st.session_state.get("erp_ifsc") or None,
            "branch": st.session_state.get("erp_branch") or None,
        },
        "line_items": line_items,
    }
    return payload, None


def main() -> None:
    init_state()

    with st.sidebar:
        st.header("ERP Settings")
        st.text_input("Backend API", key="erp_backend_api")
        st.caption("Run with: streamlit run erp_frontend.py --server.port 8502")
        if st.button("Reload Current Invoice", type="primary", use_container_width=True):
            load_current_invoice()

    st.title("ERP Invoice Form")
    st.caption("Reviewed invoice data from the invoice processing system is auto-filled here for ERP entry.")

    if st.session_state.erp_last_save_message:
        st.success(st.session_state.erp_last_save_message)

    if st.session_state.erp_loaded_source_invoice_id is None:
        load_current_invoice()

    st.info(
        f"Current source invoice: {st.session_state.get('erp_loaded_source_invoice_id') or 'Not loaded'}"
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Basic Info")
        st.text_input("Invoice Number", key="erp_invoice_number")
        st.text_input("Invoice Date", key="erp_invoice_date")
        st.text_input("Due Date", key="erp_due_date")
        st.text_input("Currency", key="erp_currency")

        st.subheader("Vendor Details")
        st.text_input("Vendor Name", key="erp_vendor_name")
        st.text_input("Vendor GST", key="erp_vendor_gst")
        st.text_area("Vendor Address", key="erp_vendor_address", height=100)

        st.subheader("Buyer Details")
        st.text_input("Buyer Name", key="erp_buyer_name")
        st.text_input("Buyer GST", key="erp_buyer_gst")
        st.text_area("Buyer Address", key="erp_buyer_address", height=100)

    with col2:
        st.subheader("Amount Details")
        st.text_input("Invoice Amount", key="erp_invoice_amount")
        st.text_input("Tax Amount", key="erp_tax_amount")
        st.text_input("Total Amount", key="erp_total_amount")
        st.text_input("Tax Rate", key="erp_tax_rate")

        st.subheader("Other Details")
        st.text_input("Payment Terms", key="erp_payment_terms")
        st.text_input("Purchase Order Number", key="erp_purchase_order_number")
        st.text_area("Notes", key="erp_notes", height=100)

        st.subheader("Bank Details")
        st.text_input("Account Number", key="erp_account_number")
        st.text_input("Account Holder", key="erp_account_holder")
        st.text_input("Bank Name", key="erp_bank_name")
        st.text_input("IFSC", key="erp_ifsc")
        st.text_input("Branch", key="erp_branch")

    with st.expander("Line Items JSON"):
        st.text_area("Line Items", key="erp_line_items", height=180)

    save_col1, save_col2 = st.columns([1, 1])
    if save_col1.button("Save", type="primary", use_container_width=True):
        payload, error = build_save_payload()
        if error:
            st.error(error)
            return
        response, save_error = post_json(
            f"{st.session_state.erp_backend_api}/erp/save_erp",
            {
                "source_invoice_id": st.session_state.get("erp_loaded_source_invoice_id"),
                "data": payload or {},
            },
        )
        if save_error:
            st.error(f"Save failed: {save_error}")
            return
        erp_record = response.get("erp_record", {}) if isinstance(response, dict) else {}
        st.session_state.erp_last_save_message = (
            f"ERP invoice saved successfully with ERP ID {erp_record.get('id', '-')}"
        )
        st.rerun()

    if save_col2.button("Preview Payload", use_container_width=True):
        payload, error = build_save_payload()
        if error:
            st.error(error)
        else:
            st.json(payload)


if __name__ == "__main__":
    main()
