import os
from typing import Any, Dict, List, Tuple
import numpy as np
from PIL import Image
import pytesseract

from backend.core.logging import logger

# Check paddle availability
HAS_PADDLE = False
try:
    from paddleocr import PaddleOCR
    HAS_PADDLE = True
except ImportError:
    HAS_PADDLE = False


class OCREngine:
    def __init__(self):
        self.paddle = None
        if HAS_PADDLE:
            try:
                self.paddle = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            except Exception as e:
                logger.warning(f"PaddleOCR init failed: {e}")

    def extract_text(self, image_np: np.ndarray) -> Dict[str, Any]:
        if self.paddle:
            try:
                result = self.paddle.ocr(image_np, cls=True)
                lines = []
                full_text = []
                if result and result[0]:
                    for line in result[0]:
                        bbox, (text, conf) = line
                        lines.append({"bbox": bbox, "text": text, "confidence": float(conf)})
                        full_text.append(text)
                return {
                    "engine": "paddle",
                    "full_text": "\n".join(full_text),
                    "lines": lines,
                }
            except Exception as exc:
                logger.warning(f"PaddleOCR extraction failed: {exc}. Falling back to Tesseract.")

        # Tesseract Fallback
        try:
            pil_img = Image.fromarray(image_np)
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            lines = []
            full_text = []
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if text:
                    full_text.append(text)
                    conf = float(data['conf'][i]) if data['conf'][i] != '-1' else 0.8
                    lines.append({
                        "bbox": [data['left'][i], data['top'][i], data['width'][i], data['height'][i]],
                        "text": text,
                        "confidence": conf / 100.0,
                    })

            joined_text = pytesseract.image_to_string(pil_img) or " ".join(full_text)
            return {
                "engine": "tesseract",
                "full_text": joined_text,
                "lines": lines,
            }
        except Exception as exc:
            logger.error(f"Tesseract OCR failed: {exc}")
            return {
                "engine": "none",
                "full_text": "",
                "lines": [],
            }


ocr_engine = OCREngine()
