from datetime import datetime
import json
from typing import Any, Dict, List, Optional

from backend.core.logging import logger
from backend.database.mysql import MySQLClient
from backend.models.inoice import ProcessingStatus


class InvoiceRepository:
    """Invoice CRUD operations with MySQL."""

    JSON_FIELDS = {"extracted_data", "confidence_scores", "ocr_result", "layout_info", "entities", "corrections"}

    @classmethod
    def _serialize_value(cls, field: str, value: Any) -> Any:
        if field in cls.JSON_FIELDS:
            if value is None:
                return None
            return json.dumps(value, default=str)
        return value

    @classmethod
    def _deserialize_value(cls, field: str, value: Any) -> Any:
        if field in cls.JSON_FIELDS and isinstance(value, str):
            try:
                return json.loads(value)
            except Exception:
                return None
        return value

    @classmethod
    def _row_to_invoice(cls, row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        invoice = dict(row)
        for field in cls.JSON_FIELDS:
            invoice[field] = cls._deserialize_value(field, invoice.get(field))
        invoice["_id"] = invoice.get("invoice_id")
        return invoice

    async def create(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.utcnow()
        record = {
            "invoice_id": invoice_data["invoice_id"],
            "user_id": str(invoice_data["user_id"]),
            "filename": invoice_data["filename"],
            "file_path": invoice_data["file_path"],
            "file_size": invoice_data["file_size"],
            "status": invoice_data.get("status", "uploaded"),
            "upload_time": invoice_data.get("upload_time") or now,
            "processing_status": invoice_data.get("processing_status", "pending"),
            "review_status": invoice_data.get("review_status"),
            "progress": invoice_data.get("progress", 0),
            "current_step": invoice_data.get("current_step"),
            "step_description": invoice_data.get("step_description"),
            "started_at": invoice_data.get("started_at"),
            "completed_at": invoice_data.get("completed_at"),
            "error_message": invoice_data.get("error_message"),
            "extracted_data": self._serialize_value("extracted_data", invoice_data.get("extracted_data")),
            "confidence_scores": self._serialize_value("confidence_scores", invoice_data.get("confidence_scores")),
            "ocr_result": self._serialize_value("ocr_result", invoice_data.get("ocr_result")),
            "layout_info": self._serialize_value("layout_info", invoice_data.get("layout_info")),
            "entities": self._serialize_value("entities", invoice_data.get("entities")),
            "reviewed_by": invoice_data.get("reviewed_by"),
            "reviewed_at": invoice_data.get("reviewed_at"),
            "corrections": self._serialize_value("corrections", invoice_data.get("corrections")),
            "review_notes": invoice_data.get("review_notes"),
            "created_at": invoice_data.get("created_at") or now,
            "updated_at": invoice_data.get("updated_at") or now,
            "last_updated": invoice_data.get("last_updated"),
        }

        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO invoices (
                        invoice_id, user_id, filename, file_path, file_size, status,
                        upload_time, processing_status, review_status, progress,
                        current_step, step_description, started_at, completed_at, error_message,
                        extracted_data, confidence_scores, ocr_result, layout_info, entities,
                        reviewed_by, reviewed_at, corrections, review_notes,
                        created_at, updated_at, last_updated
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s
                    )
                    """,
                    (
                        record["invoice_id"],
                        record["user_id"],
                        record["filename"],
                        record["file_path"],
                        record["file_size"],
                        record["status"],
                        record["upload_time"],
                        record["processing_status"],
                        record["review_status"],
                        record["progress"],
                        record["current_step"],
                        record["step_description"],
                        record["started_at"],
                        record["completed_at"],
                        record["error_message"],
                        record["extracted_data"],
                        record["confidence_scores"],
                        record["ocr_result"],
                        record["layout_info"],
                        record["entities"],
                        record["reviewed_by"],
                        record["reviewed_at"],
                        record["corrections"],
                        record["review_notes"],
                        record["created_at"],
                        record["updated_at"],
                        record["last_updated"],
                    ),
                )

        logger.info("Invoice created: %s", record["invoice_id"])
        created = await self.get_by_id(record["invoice_id"])
        if not created:
            raise RuntimeError("Failed to fetch created invoice")
        return created

    async def get_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT * FROM invoices WHERE invoice_id = %s LIMIT 1",
                    (invoice_id,),
                )
                row = await cur.fetchone()
        return self._row_to_invoice(row)

    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        pool = MySQLClient.get_pool()
        query = "SELECT * FROM invoices WHERE user_id = %s"
        params: List[Any] = [str(user_id)]
        if status:
            query += " AND processing_status = %s"
            params.append(status)
        query += " ORDER BY upload_time DESC LIMIT %s OFFSET %s"
        params.extend([int(limit), int(skip)])

        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, tuple(params))
                rows = await cur.fetchall()
        return [inv for inv in (self._row_to_invoice(row) for row in rows) if inv is not None]

    async def update(
        self,
        invoice_id: str,
        update_data: Dict[str, Any],
        return_updated: bool = True,
    ) -> Dict[str, Any]:
        field_map = {
            "user_id": "user_id",
            "filename": "filename",
            "file_path": "file_path",
            "file_size": "file_size",
            "status": "status",
            "upload_time": "upload_time",
            "processing_status": "processing_status",
            "review_status": "review_status",
            "progress": "progress",
            "current_step": "current_step",
            "step_description": "step_description",
            "started_at": "started_at",
            "completed_at": "completed_at",
            "error_message": "error_message",
            "extracted_data": "extracted_data",
            "confidence_scores": "confidence_scores",
            "ocr_result": "ocr_result",
            "layout_info": "layout_info",
            "entities": "entities",
            "reviewed_by": "reviewed_by",
            "reviewed_at": "reviewed_at",
            "corrections": "corrections",
            "review_notes": "review_notes",
            "last_updated": "last_updated",
        }

        assignments = []
        values = []
        for key, value in update_data.items():
            column = field_map.get(key)
            if not column:
                continue
            assignments.append(f"{column} = %s")
            values.append(self._serialize_value(key, value))

        if not assignments:
            existing = await self.get_by_id(invoice_id)
            if not existing:
                raise ValueError(f"Invoice not found: {invoice_id}")
            return existing

        assignments.append("updated_at = %s")
        values.append(datetime.utcnow())
        values.append(invoice_id)

        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"UPDATE invoices SET {', '.join(assignments)} WHERE invoice_id = %s",
                    tuple(values),
                )
                if cur.rowcount == 0:
                    raise ValueError(f"Invoice not found: {invoice_id}")

        logger.info("Invoice updated: %s", invoice_id)
        if not return_updated:
            return {"invoice_id": invoice_id}
        updated = await self.get_by_id(invoice_id)
        if not updated:
            raise ValueError(f"Invoice not found: {invoice_id}")
        return updated

    async def update_status(self, invoice_id: str, status: ProcessingStatus, **kwargs) -> Dict[str, Any]:
        update_data = {"processing_status": status.value, **kwargs}
        return await self.update(invoice_id, update_data)

    async def delete(self, invoice_id: str) -> bool:
        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM invoices WHERE invoice_id = %s", (invoice_id,))
                if cur.rowcount == 0:
                    raise ValueError(f"Invoice not found: {invoice_id}")
        logger.info("Invoice deleted: %s", invoice_id)
        return True

    async def count_by_user(self, user_id: str) -> int:
        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT COUNT(*) AS count FROM invoices WHERE user_id = %s", (str(user_id),))
                row = await cur.fetchone()
        return int((row or {}).get("count", 0))

    async def get_statistics(self, user_id: str) -> Dict[str, Any]:
        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT processing_status AS status, COUNT(*) AS count
                    FROM invoices
                    WHERE user_id = %s
                    GROUP BY processing_status
                    """,
                    (str(user_id),),
                )
                rows = await cur.fetchall()
        return {row["status"]: row["count"] for row in rows}

