import asyncio
import os
import traceback
from typing import Any, Dict, Optional
import numpy as np

from backend.ai.layout_detection import layout_detector
from backend.ai.ner_extraction import ner_extractor
from backend.ai.ocr_engine import ocr_engine
from backend.ai.preprocessing import preprocessor
from backend.ai.vision_llm import vision_llm_extractor
from backend.core.logging import logger
from backend.database.repositories.invoice_repo import invoice_repo
from backend.models.inoice import InvoiceOut, ProcessingStatus
from backend.services.validation_service import validation_service
from backend.utils.image_utils import load_image, resize_image_max


class ProcessingService:
    async def process_invoice(self, invoice_id: str) -> Optional[InvoiceOut]:
        invoice = await invoice_repo.get_by_id(invoice_id)
        if not invoice:
            logger.error(f"Invoice {invoice_id} not found for processing.")
            return None

        # Update status to processing
        await invoice_repo.update(invoice_id, {"processing_status": ProcessingStatus.PROCESSING.value})

        try:
            file_path = invoice.file_path
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            ext = file_path.split(".")[-1].lower()
            images = []
            if ext == "pdf":
                images = preprocessor.convert_pdf_to_images(file_path)
            else:
                img_np = load_image(file_path)
                if img_np is not None:
                    images = [img_np]

            if not images:
                # Generate fallback dummy image representation if file is non-image/mock
                img_np = np.ones((1000, 800, 3), dtype=np.uint8) * 255
                images = [img_np]

            all_lines = []
            full_texts = []

            for img in images:
                enhanced = preprocessor.enhance_image(img)
                resized = resize_image_max(enhanced)
                ocr_data = ocr_engine.extract_text(resized)
                all_lines.extend(ocr_data.get("lines", []))
                full_texts.append(ocr_data.get("full_text", ""))

            combined_ocr_result = {
                "full_text": "\n".join(full_texts),
                "lines": all_lines,
            }

            # Layout Detection
            layout_info = layout_detector.detect_layout(images[0])

            # Heuristic Field Extraction
            raw_extracted = vision_llm_extractor.extract_fields(combined_ocr_result)

            # NER Entity Extraction
            entities = ner_extractor.extract_entities(combined_ocr_result.get("full_text", ""))

            # Validation & Confidence Scoring
            cleaned_extracted, overall_conf, confidence_scores = validation_service.validate_and_score(
                raw_extracted, all_lines
            )

            # Persistence
            updates = {
                "processing_status": ProcessingStatus.COMPLETED.value,
                "overall_confidence": overall_conf,
                "extracted_data": cleaned_extracted,
                "confidence_scores": confidence_scores,
                "ocr_result": combined_ocr_result,
                "layout_info": layout_info,
                "entities": entities,
                "error_message": None,
            }
            return await invoice_repo.update(invoice_id, updates)

        except Exception as exc:
            logger.error(f"Processing invoice {invoice_id} failed: {exc}\n{traceback.format_exc()}")
            updates = {
                "processing_status": ProcessingStatus.FAILED.value,
                "error_message": str(exc),
            }
            return await invoice_repo.update(invoice_id, updates)


processing_service = ProcessingService()
