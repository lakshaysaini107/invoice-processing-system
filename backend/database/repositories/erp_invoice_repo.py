from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from backend.database.mysql import MySQLClient


class ERPInvoiceRepository:
    """Persist ERP-ready invoice records."""

    @staticmethod
    def _none_if_blank(value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    async def save(self, source_invoice_id: Optional[str], data: Dict[str, Any]) -> Dict[str, Any]:
        bank_details = data.get("bank_details") if isinstance(data.get("bank_details"), dict) else {}
        now = datetime.utcnow()

        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO erp_invoices (
                        source_invoice_id,
                        invoice_number, invoice_date, due_date,
                        vendor_name, vendor_gst, vendor_address,
                        buyer_name, buyer_gst, buyer_address,
                        invoice_amount, tax_amount, total_amount,
                        tax_rate, currency, payment_terms,
                        purchase_order_number,
                        account_number, account_holder, bank_name, ifsc, branch,
                        notes, created_at, updated_at
                    ) VALUES (
                        %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    """,
                    (
                        self._none_if_blank(source_invoice_id),
                        self._none_if_blank(data.get("invoice_number")),
                        self._none_if_blank(data.get("invoice_date")),
                        self._none_if_blank(data.get("due_date")),
                        self._none_if_blank(data.get("vendor_name")),
                        self._none_if_blank(data.get("vendor_gst")),
                        self._none_if_blank(data.get("vendor_address")),
                        self._none_if_blank(data.get("buyer_name")),
                        self._none_if_blank(data.get("buyer_gst")),
                        self._none_if_blank(data.get("buyer_address")),
                        data.get("invoice_amount"),
                        data.get("tax_amount"),
                        data.get("total_amount"),
                        data.get("tax_rate"),
                        self._none_if_blank(data.get("currency")),
                        self._none_if_blank(data.get("payment_terms")),
                        self._none_if_blank(data.get("purchase_order_number")),
                        self._none_if_blank(bank_details.get("account_number")),
                        self._none_if_blank(bank_details.get("account_holder")),
                        self._none_if_blank(bank_details.get("bank_name")),
                        self._none_if_blank(bank_details.get("ifsc")),
                        self._none_if_blank(bank_details.get("branch")),
                        self._none_if_blank(data.get("notes")),
                        now,
                        now,
                    ),
                )
                erp_id = cur.lastrowid

        return {
            "id": erp_id,
            "source_invoice_id": source_invoice_id,
            "saved_at": now.isoformat(),
        }
