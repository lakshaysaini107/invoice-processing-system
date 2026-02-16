import os
import shutil
import pytesseract
import numpy as np
from typing import Dict, Any, Optional
from pytesseract import Output
from backend.core.logging import logger
from backend.app.config import settings

class OCREngine:
    """Extract text from invoice images using Tesseract + PaddleOCR"""

    def __init__(self, use_paddle: bool = True):
        self.use_paddle = use_paddle
        self.paddle_ocr = None
        if use_paddle:
            try:
                from paddleocr import PaddleOCR  # lazy import
                self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang='en')
            except Exception as e:
                logger.warning(
                    f"PaddleOCR not available, falling back to Tesseract. Reason: {str(e)}"
                )
                self.use_paddle = False

        # Configure Tesseract path (optional)
        self.tesseract_cmd = self._resolve_tesseract_cmd()
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        else:
            logger.warning("Tesseract executable not found. Set TESSERACT_CMD or add it to PATH.")

        # Configure tessdata path if available
        tessdata_prefix = self._resolve_tessdata_prefix()
        if tessdata_prefix:
            os.environ["TESSDATA_PREFIX"] = tessdata_prefix

        # Tesseract configuration
        self.base_config = "--oem 3 -l eng"
        self.psm_modes = [6, 4, 3, 11]

    def _resolve_tesseract_cmd(self) -> Optional[str]:
        env_cmd = os.getenv("TESSERACT_CMD") or getattr(settings, "TESSERACT_CMD", "")
        if env_cmd and os.path.exists(env_cmd):
            return env_cmd

        # Common Windows install locations
        default_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        for path in default_paths:
            if os.path.exists(path):
                return path

        detected = shutil.which("tesseract")
        if detected:
            return detected

        return None

    def _resolve_tessdata_prefix(self) -> Optional[str]:
        env_prefix = os.getenv("TESSDATA_PREFIX") or getattr(settings, "TESSDATA_PREFIX", "")
        if env_prefix and os.path.isdir(env_prefix):
            return env_prefix

        if self.tesseract_cmd:
            candidate = os.path.join(os.path.dirname(self.tesseract_cmd), "tessdata")
            if os.path.isdir(candidate):
                return candidate

        return None

    def _build_config(self, psm: int) -> str:
        return f"{self.base_config} --psm {psm}"

    def _avg_confidence(self, data: Dict[str, Any]) -> float:
        confidences = []
        for conf in data.get("conf", []):
            try:
                value = float(conf)
            except (TypeError, ValueError):
                continue
            if value >= 0:
                confidences.append(value / 100)
        return sum(confidences) / len(confidences) if confidences else 0.0

    async def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract text with confidence scores
        Returns structured OCR result
        """
        try:
            if self.use_paddle:
                return await self._paddle_ocr(image)
            return await self._tesseract_ocr(image)

        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            raise

    async def _paddle_ocr(self, image: np.ndarray) -> Dict[str, Any]:
        """PaddleOCR extraction (more accurate for complex layouts)"""
        result = self.paddle_ocr.ocr(image, cls=True)

        extracted_text = ""
        text_boxes = []
        total_confidence = 0.0

        # Flatten results list which can be nested depending on version
        if result and isinstance(result[0], list):
            for line in result:
                if line:
                    for word_info in line:
                        box, (text, conf) = word_info
                        extracted_text += text + " "
                        text_boxes.append({
                            "text": text,
                            "confidence": float(conf),
                            "bbox": box
                        })
                        total_confidence += conf

        avg_confidence = total_confidence / len(text_boxes) if text_boxes else 0.0

        return {
            "text": extracted_text.strip(),
            "boxes": text_boxes,
            "average_confidence": avg_confidence,
            "engine": "PaddleOCR"
        }

    async def _tesseract_ocr(self, image: np.ndarray) -> Dict[str, Any]:
        """Tesseract OCR extraction (faster, lower accuracy)"""
        best = None

        for psm in self.psm_modes:
            config = self._build_config(psm)
            data = pytesseract.image_to_data(image, config=config, output_type=Output.DICT)
            avg_conf = self._avg_confidence(data)
            text_len = sum(len(str(t)) for t in data.get("text", []) if str(t).strip())
            score = (avg_conf, text_len)

            if best is None or score > best["score"]:
                best = {
                    "psm": psm,
                    "data": data,
                    "score": score,
                    "avg_conf": avg_conf,
                }

        if best is None:
            raise RuntimeError("Tesseract OCR failed to produce any output")

        # Use the best PSM config for the final text output
        best_config = self._build_config(best["psm"])
        text = pytesseract.image_to_string(image, config=best_config)

        data = best["data"]
        text_boxes = []
        confidences = []

        for i in range(len(data.get('text', []))):
            word = str(data['text'][i]).strip()
            if word:
                conf = float(data['conf'][i]) if str(data['conf'][i]).strip() else -1
                if conf >= 0:
                    confidences.append(conf / 100)
                text_boxes.append({
                    "text": word,
                    "confidence": conf / 100 if conf >= 0 else 0.0,
                    "bbox": {
                        "x": data['left'][i],
                        "y": data['top'][i],
                        "w": data['width'][i],
                        "h": data['height'][i]
                    }
                })

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return {
            "text": text,
            "boxes": text_boxes,
            "average_confidence": avg_confidence,
            "engine": "Tesseract"
        }
