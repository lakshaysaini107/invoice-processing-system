from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Tuple

import requests
import streamlit as st
from requests import RequestException


DEFAULT_BACKEND_API = os.getenv("ERP_BACKEND_API", "http://localhost:8000/api")


st.set_page_config(page_title="ERP Invoice Form", layout="wide")


def apply_erp_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Manrope:wght@400;500;600;700&display=swap');

        :root {
            --erp-bg: #f4efe6;
            --erp-ink: #172126;
            --erp-muted: #5f6b73;
            --erp-card: rgba(255, 255, 255, 0.82);
            --erp-border: rgba(23, 33, 38, 0.10);
            --erp-deep: #0f3d56;
            --erp-amber: #e8a547;
            --erp-mint: #1f8a70;
            --erp-danger: #c75b39;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(232, 165, 71, 0.16), transparent 26%),
                radial-gradient(circle at top right, rgba(15, 61, 86, 0.16), transparent 24%),
                linear-gradient(180deg, #f6f0e7 0%, #f1f6f5 100%);
        }

        html, body, [class*="css"]  {
            font-family: "Manrope", sans-serif;
            color: var(--erp-ink);
        }

        h1, h2, h3 {
            font-family: "Space Grotesk", sans-serif !important;
            color: var(--erp-ink);
            letter-spacing: -0.02em;
        }

        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.72);
            border-right: 1px solid var(--erp-border);
        }

        [data-testid="stHeader"] {
            background: rgba(244, 239, 230, 0.72);
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stTextArea"] textarea {
            border-radius: 14px;
            border: 1px solid rgba(23, 33, 38, 0.14);
            background: rgba(255, 255, 255, 0.92);
        }

        div[data-testid="stTextInput"] input:focus,
        div[data-testid="stTextArea"] textarea:focus {
            border-color: rgba(15, 61, 86, 0.42);
            box-shadow: 0 0 0 0.2rem rgba(15, 61, 86, 0.08);
        }

        div.stButton > button, div.stLinkButton > a {
            border-radius: 14px !important;
            font-weight: 700 !important;
            border: 0 !important;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, var(--erp-deep), #155e75) !important;
            color: white !important;
            box-shadow: 0 12px 24px rgba(15, 61, 86, 0.18);
        }

        div.stButton > button:not([kind="primary"]) {
            background: rgba(15, 61, 86, 0.08) !important;
            color: var(--erp-deep) !important;
        }

        .erp-hero {
            border: 1px solid var(--erp-border);
            border-radius: 24px;
            padding: 1.5rem 1.6rem;
            background: linear-gradient(130deg, rgba(255,255,255,0.86), rgba(247,250,249,0.78));
            box-shadow: 0 24px 44px rgba(15, 61, 86, 0.08);
            margin-bottom: 1rem;
        }

        .erp-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            border-radius: 999px;
            padding: 0.45rem 0.8rem;
            background: rgba(15, 61, 86, 0.08);
            color: var(--erp-deep);
            font-size: 0.76rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .erp-hero h1 {
            margin: 0.9rem 0 0.35rem 0;
            font-size: clamp(2rem, 4vw, 3.2rem);
        }

        .erp-hero p {
            margin: 0;
            color: var(--erp-muted);
            font-size: 1rem;
            line-height: 1.7;
            max-width: 60ch;
        }

        .erp-kpi {
            border: 1px solid var(--erp-border);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            background: var(--erp-card);
            box-shadow: 0 16px 28px rgba(15, 61, 86, 0.06);
        }

        .erp-kpi-label {
            color: var(--erp-muted);
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }

        .erp-kpi-value {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.25rem;
            color: var(--erp-ink);
        }

        .erp-section-title {
            margin: 0 0 0.2rem 0;
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.05rem;
        }

        .erp-section-copy {
            margin: 0 0 0.85rem 0;
            color: var(--erp-muted);
            font-size: 0.9rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "erp_backend_api" not in st.session_state:
        st.session_state.erp_backend_api = DEFAULT_BACKEND_API
    if "erp_target_invoice_id" not in st.session_state:
        st.session_state.erp_target_invoice_id = None
    if "erp_query_signature" not in st.session_state:
        st.session_state.erp_query_signature = None
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

def response_error(payload: Any) -> str:
    if isinstance(payload, dict):
        detail = payload.get("detail") or payload.get("error") or payload.get("message")
        if detail is not None:
            return str(detail)
    return str(payload)


def get_json(url: str, timeout: float = 10.0) -> Tuple[Optional[Any], Optional[str]]:
    try:
        response = requests.get(url, timeout=timeout)
    except RequestException as exc:
        return None, str(exc)
    payload = decode_response_json(response)
    if response.ok:
        return payload, None
    return None, response_error(payload)


def post_json(
    url: str,
    payload: Dict[str, Any],
    timeout: float = 15.0,
) -> Tuple[Optional[Any], Optional[str]]:
    try:
        response = requests.post(url, json=payload, timeout=timeout)
    except RequestException as exc:
        return None, str(exc)
    decoded = decode_response_json(response)
    if response.ok:
        return decoded, None
    return None, response_error(decoded)


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


def _query_param_value(name: str) -> Optional[str]:
    try:
        value = st.query_params.get(name)
    except Exception:
        return None
    if isinstance(value, list):
        value = value[0] if value else None
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def apply_query_context() -> None:
    backend_api = _query_param_value("backend_api")
    invoice_id = _query_param_value("invoice_id")
    signature = (backend_api, invoice_id)
    if signature == st.session_state.get("erp_query_signature"):
        return

    if backend_api:
        st.session_state.erp_backend_api = backend_api.rstrip("/")
    if invoice_id:
        st.session_state.erp_target_invoice_id = invoice_id

    st.session_state.erp_query_signature = signature


def populate_invoice_state(payload: Dict[str, Any]) -> None:
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


def load_current_invoice(invoice_id: Optional[str] = None) -> None:
    target_invoice_id = invoice_id or st.session_state.get("erp_target_invoice_id")

    if target_invoice_id:
        payload, error = get_json(f"{st.session_state.erp_backend_api}/erp/invoice/{target_invoice_id}")
        if error is None and isinstance(payload, dict):
            populate_invoice_state(payload)
            return

        _, set_error = post_json(
            f"{st.session_state.erp_backend_api}/erp/set_current_invoice",
            {"invoice_id": target_invoice_id},
        )
        if set_error:
            st.error(f"Could not load invoice {target_invoice_id}: {error or set_error}")
            return

    payload, error = get_json(f"{st.session_state.erp_backend_api}/erp/get_current_invoice")
    if error:
        message = f"Could not load current invoice: {error}"
        if target_invoice_id:
            message = f"Could not load invoice {target_invoice_id}: {error}"
        st.error(message)
        return
    if not isinstance(payload, dict):
        st.error("Unexpected ERP handoff payload.")
        return

    populate_invoice_state(payload)


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


def _display_value(value: Any, fallback: str = "-") -> str:
    text = str(value).strip() if value is not None else ""
    return text or fallback


def _numeric_snapshot(value: Any) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        return "-"
    try:
        return f"₹{float(text.replace(',', '')):,.2f}"
    except ValueError:
        return text


def _line_item_count() -> int:
    try:
        payload = json.loads(st.session_state.get("erp_line_items", "") or "[]")
    except json.JSONDecodeError:
        return 0
    return len(payload) if isinstance(payload, list) else 0


def render_hero() -> None:
    st.markdown(
        """
        <div class="erp-hero">
          <div class="erp-eyebrow">ERP Handoff</div>
          <h1>Review-ready invoice data, reshaped for ERP entry.</h1>
          <p>
            This workspace receives the reviewed invoice from the processing system, auto-fills the ERP form,
            and lets your team make final edits before writing a clean record into MySQL.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_snapshot_metrics() -> None:
    metrics = [
        ("Source Invoice", _display_value(st.session_state.get("erp_loaded_source_invoice_id"))),
        ("Vendor", _display_value(st.session_state.get("erp_vendor_name"))),
        ("Total Amount", _numeric_snapshot(st.session_state.get("erp_total_amount"))),
        ("Line Items", str(_line_item_count())),
    ]
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.markdown(
            f"""
            <div class="erp-kpi">
              <div class="erp-kpi-label">{label}</div>
              <div class="erp-kpi-value">{value}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def section_intro(title: str, copy: str) -> None:
    st.markdown(f"<div class='erp-section-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='erp-section-copy'>{copy}</div>", unsafe_allow_html=True)


def main() -> None:
    init_state()
    apply_erp_theme()
    apply_query_context()

    with st.sidebar:
        st.header("ERP Settings")
        st.text_input("Backend API", key="erp_backend_api")
        st.caption("Run with: streamlit run erp_frontend.py --server.port 8503")
        st.text_input("Target Invoice ID", key="erp_target_invoice_id")
        if st.button("Reload Current Invoice", type="primary", use_container_width=True):
            load_current_invoice(st.session_state.get("erp_target_invoice_id"))

    st.title("ERP Invoice Form")
    st.caption("Reviewed invoice data from the invoice processing system is auto-filled here for ERP entry without a separate ERP sign-in.")

    if st.session_state.erp_last_save_message:
        st.success(st.session_state.erp_last_save_message)

    target_invoice_id = st.session_state.get("erp_target_invoice_id")
    if (
        target_invoice_id
        and target_invoice_id != st.session_state.get("erp_loaded_source_invoice_id")
    ):
        load_current_invoice(target_invoice_id)
    elif st.session_state.erp_loaded_source_invoice_id is None:
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
