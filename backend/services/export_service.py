import csv
import io
import json
from typing import Any, Dict, List, Tuple
from openpyxl import Workbook
from backend.core.exceptions import NotFoundException
from backend.database.repositories.invoice_repo import invoice_repo


class ExportService:
    async def export_single_invoice(self, invoice_id: str, fmt: str = "json") -> Tuple[bytes, str, str]:
        invoice = await invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundException(f"Invoice {invoice_id} not found.")

        fmt = fmt.lower().strip()
        data = invoice.extracted_data or {}
        filename = f"invoice_{invoice.id[:8]}"

        if fmt == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Field", "Value"])
            for k, v in data.items():
                if not isinstance(v, (dict, list)):
                    writer.writerow([k, v])
            content = output.getvalue().encode("utf-8")
            return content, f"{filename}.csv", "text/csv"

        elif fmt in ["xlsx", "excel"]:
            wb = Workbook()
            ws = wb.active
            ws.title = "Invoice Details"
            ws.append(["Field", "Value"])
            for k, v in data.items():
                if not isinstance(v, (dict, list)):
                    ws.append([k, str(v) if v is not None else ""])
            output = io.BytesIO()
            wb.save(output)
            return output.getvalue(), f"{filename}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        else:
            payload = {
                "id": invoice.id,
                "filename": invoice.filename,
                "processing_status": invoice.processing_status,
                "overall_confidence": invoice.overall_confidence,
                "extracted_data": data,
                "confidence_scores": invoice.confidence_scores,
            }
            content = json.dumps(payload, indent=2).encode("utf-8")
            return content, f"{filename}.json", "application/json"


export_service = ExportService()
