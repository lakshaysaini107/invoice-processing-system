from datetime import datetime
from typing import Optional
from backend.core.logging import logger
from backend.database.repositories.invoice_repo import InvoiceRepository
from backend.ai.preprocessing import PreprocessingEngine
from backend.ai.ocr_engine import OCREngine
from backend.ai.layout_detection import LayoutDetectionEngine
from backend.ai.vision_llm import VisionLLMEngine
from backend.ai.ner_extraction import NEREngine
from backend.services.validation_service import ValidationService
from backend.app.config import settings
import asyncio

class ProcessingService:
    """Orchestrate complete invoice processing pipeline"""

    def __init__(
        self,
        invoice_repo: InvoiceRepository,
        preprocessing: PreprocessingEngine,
        ocr: OCREngine,
        layout_detection: LayoutDetectionEngine,
        vision_llm: VisionLLMEngine,
        ner: NEREngine,
        validation: ValidationService
    ):
        self.invoice_repo = invoice_repo
        self.preprocessing = preprocessing
        self.ocr = ocr
        self.layout_detection = layout_detection
        self.vision_llm = vision_llm
        self.ner = ner
        self.validation = validation

    async def process_invoice(
        self,
        invoice_id: str,
        file_path: str,
        use_cache: bool = True
    ) -> dict:
        """
        Complete pipeline:
        1. Preprocessing (Image enhancement)
        2. OCR (Text extraction)
        3. Layout Detection (Table/structure identification)
        4. Vision LLM (Field extraction with context)
        5. NER (Entity recognition)
        6. Validation (Accuracy checks)
        """
        
        try:
            # Step 1: Preprocessing
            await self._update_progress(invoice_id, 10, "preprocessing", "Image enhancement")
            processed_image = await self.preprocessing.process_image(file_path)
            logger.info(f"Preprocessing completed for {invoice_id}")

            # Step 2: OCR
            await self._update_progress(invoice_id, 25, "ocr", "Extracting text")
            ocr_result = await self.ocr.extract_text(processed_image)
            raw_text = ocr_result["text"]
            logger.info(f"OCR completed - Extracted {len(raw_text)} characters")

            # Step 3: Layout Detection
            await self._update_progress(invoice_id, 40, "layout_detection", "Detecting structure")
            layout_info = await self.layout_detection.detect_layout(processed_image)
            logger.info(f"Layout detected: {len(layout_info.get('tables', []))} tables found")

            # Step 4: Vision LLM for structured extraction
            await self._update_progress(invoice_id, 55, "vision_llm", "Extracting fields")
            extracted_fields = await self.vision_llm.extract_fields(
                image=processed_image,
                ocr_text=raw_text,
                layout_info=layout_info
            )
            logger.info(f"Vision LLM extraction completed")

            # Step 5: NER for entity recognition
            await self._update_progress(invoice_id, 70, "ner", "Recognizing entities")
            entities = await self.ner.extract_entities(raw_text, extracted_fields)
            logger.info(f"NER completed - Found {len(entities)} entities")

            # Step 6: Validation & Confidence Scoring
            await self._update_progress(invoice_id, 85, "validation", "Validating data")
            validated_data, confidence_scores = await self.validation.validate_extraction(
                extracted_fields=extracted_fields,
                entities=entities,
                raw_text=raw_text
            )
            logger.info(f"Validation completed - Accuracy: {confidence_scores.get('overall', 0):.2%}")

            # Finalize
            await self._update_progress(invoice_id, 100, "completed", "Processing complete")
            
            # Save results
            await self.invoice_repo.update(
                invoice_id,
                {
                    "processing_status": "completed",
                    "extracted_data": validated_data,
                    "confidence_scores": confidence_scores,
                    "ocr_result": ocr_result,
                    "layout_info": layout_info,
                    "entities": entities,
                    "completed_at": datetime.utcnow(),
                    # "processing_time": "N/A" # Calculate from timestamps if needed
                }
            )
            
            logger.info(f"Invoice {invoice_id} processing completed successfully")
            return {
                "status": "completed",
                "invoice_id": invoice_id,
                "extracted_data": validated_data,
                "confidence_scores": confidence_scores
            }

        except Exception as e:
            logger.error(f"Processing failed for {invoice_id}: {str(e)}")
            await self.invoice_repo.update(
                invoice_id,
                {
                    "processing_status": "failed",
                    "error_message": str(e),
                    "completed_at": datetime.utcnow()
                }
            )
            raise

    async def _update_progress(
        self,
        invoice_id: str,
        progress: int,
        current_step: str,
        description: str
    ):
        """Update processing progress"""
        await self.invoice_repo.update(
            invoice_id,
            {
                "progress": progress,
                "current_step": current_step,
                "step_description": description,
                "last_updated": datetime.utcnow()
            }
        )
