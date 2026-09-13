import json
from typing import Any, Dict, List, Optional
from backend.database.mysql import db_manager


class ERPInvoiceRepository:
    def _parse_json_field(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return None
        return value

    async def save(self, data: Dict[str, Any], source_invoice_id: Optional[str] = None) -> Dict[str, Any]:
        query = """
        INSERT INTO erp_invoices (
            source_invoice_id, invoice_number, invoice_date, due_date,
            vendor_name, vendor_gst, vendor_address,
            buyer_name, buyer_gst, buyer_address,
            invoice_amount, tax_amount, total_amount, tax_rate,
            currency, payment_terms, purchase_order_number, notes,
            bank_details, line_items
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """
        bank_details_json = json.dumps(data.get("bank_details") or {})
        line_items_json = json.dumps(data.get("line_items") or [])

        res = await db_manager.execute_query(
            query,
            (
                source_invoice_id,
                data.get("invoice_number"),
                data.get("invoice_date"),
                data.get("due_date"),
                data.get("vendor_name"),
                data.get("vendor_gst"),
                data.get("vendor_address"),
                data.get("buyer_name"),
                data.get("buyer_gst"),
                data.get("buyer_address"),
                data.get("invoice_amount"),
                data.get("tax_amount"),
                data.get("total_amount"),
                data.get("tax_rate"),
                data.get("currency"),
                data.get("payment_terms"),
                data.get("purchase_order_number"),
                data.get("notes"),
                bank_details_json,
                line_items_json,
            ),
        )

        erp_id = res[0].get("lastrowid") if res else 1
        return await self.get_by_id(erp_id) or {"id": erp_id, "source_invoice_id": source_invoice_id, **data}

    async def get_by_id(self, erp_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM erp_invoices WHERE id = %s"
        rows = await db_manager.execute_query(query, (erp_id,))
        if not rows:
            return None
        row = rows[0]
        row["bank_details"] = self._parse_json_field(row.get("bank_details"))
        row["line_items"] = self._parse_json_field(row.get("line_items"))
        return row

    async def get_latest_by_source_id(self, source_invoice_id: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM erp_invoices WHERE source_invoice_id = %s ORDER BY id DESC LIMIT 1"
        rows = await db_manager.execute_query(query, (source_invoice_id,))
        if not rows:
            return None
        row = rows[0]
        row["bank_details"] = self._parse_json_field(row.get("bank_details"))
        row["line_items"] = self._parse_json_field(row.get("line_items"))
        return row


erp_invoice_repo = ERPInvoiceRepository()
