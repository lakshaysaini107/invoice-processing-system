import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from backend.database.mysql import db_manager
from backend.models.inoice import InvoiceCreate, InvoiceOut, ProcessingStatus, ReviewStatus


class InvoiceRepository:
    def _parse_json_field(self, value: Any) -> Any:
        if value is None:
            return {}
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return {}
        return {}

    def _row_to_invoice(self, row: Dict[str, Any]) -> InvoiceOut:
        return InvoiceOut(
            id=str(row.get("id")),
            user_id=row.get("user_id"),
            filename=str(row.get("filename", "")),
            file_path=str(row.get("file_path", "")),
            file_size=int(row.get("file_size", 0)),
            upload_timestamp=row.get("upload_timestamp"),
            processing_status=row.get("processing_status", ProcessingStatus.PENDING.value),
            overall_confidence=float(row.get("overall_confidence") or 0.0),
            extracted_data=self._parse_json_field(row.get("extracted_data")),
            confidence_scores=self._parse_json_field(row.get("confidence_scores")),
            ocr_result=self._parse_json_field(row.get("ocr_result")),
            layout_info=self._parse_json_field(row.get("layout_info")),
            entities=self._parse_json_field(row.get("entities")),
            corrections=self._parse_json_field(row.get("corrections")) if isinstance(self._parse_json_field(row.get("corrections")), list) else [],
            review_status=row.get("review_status", ReviewStatus.UNREVIEWED.value),
            reviewed_by=row.get("reviewed_by"),
            reviewed_at=row.get("reviewed_at"),
            review_notes=row.get("review_notes"),
            error_message=row.get("error_message"),
        )

    async def create(self, invoice_in: InvoiceCreate) -> InvoiceOut:
        invoice_id = str(uuid.uuid4())
        query = """
        INSERT INTO invoices (id, user_id, filename, file_path, file_size, processing_status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        await db_manager.execute_query(
            query,
            (
                invoice_id,
                invoice_in.user_id,
                invoice_in.filename,
                invoice_in.file_path,
                invoice_in.file_size,
                ProcessingStatus.PENDING.value,
            ),
        )
        return await self.get_by_id(invoice_id)

    async def get_by_id(self, invoice_id: str) -> Optional[InvoiceOut]:
        query = "SELECT * FROM invoices WHERE id = %s"
        rows = await db_manager.execute_query(query, (invoice_id,))
        if not rows:
            return None
        return self._row_to_invoice(rows[0])

    async def list_all(self, user_id: Optional[str] = None, limit: int = 100) -> List[InvoiceOut]:
        if user_id:
            query = "SELECT * FROM invoices WHERE user_id = %s ORDER BY upload_timestamp DESC LIMIT %s"
            rows = await db_manager.execute_query(query, (user_id, limit))
        else:
            query = "SELECT * FROM invoices ORDER BY upload_timestamp DESC LIMIT %s"
            rows = await db_manager.execute_query(query, (limit,))
        return [self._row_to_invoice(r) for r in rows]

    async def update(self, invoice_id: str, updates: Dict[str, Any]) -> Optional[InvoiceOut]:
        if not updates:
            return await self.get_by_id(invoice_id)

        set_clause = []
        params = []
        for key, value in updates.items():
            set_clause.append(f"{key} = %s")
            if isinstance(value, (dict, list)):
                params.append(json.dumps(value))
            else:
                params.append(value)

        params.append(invoice_id)
        query = f"UPDATE invoices SET {', '.join(set_clause)} WHERE id = %s"
        await db_manager.execute_query(query, tuple(params))
        return await self.get_by_id(invoice_id)

    async def delete(self, invoice_id: str) -> bool:
        query = "DELETE FROM invoices WHERE id = %s"
        await db_manager.execute_query(query, (invoice_id,))
        return True


invoice_repo = InvoiceRepository()
