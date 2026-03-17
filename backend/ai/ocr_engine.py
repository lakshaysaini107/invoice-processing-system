import os
import re
import shutil
import importlib.util
import pytesseract
import cv2
import numpy as np
from typing import Dict, Any, Optional
from pytesseract import Output
from backend.core.logging import logger
from backend.app.config import settings
from backend.utils.regex_utils import REGEX_PATTERNS

class OCREngine:
    """Extract text from invoice images using Tesseract + PaddleOCR"""

    def __init__(self, use_paddle: bool = True):
        self.use_paddle = use_paddle
        self.paddle_ocr = None
        if use_paddle and self._paddle_runtime_available():
            try:
                # Skip remote model source reachability checks on startup.
                os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
                from paddleocr import PaddleOCR  # lazy import
                self.paddle_ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
            except Exception as e:
                logger.warning(
                    f"PaddleOCR not available, falling back to Tesseract. Reason: {str(e)}"
                )
                self.use_paddle = False
        elif use_paddle:
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
        self.psm_modes = [6, 4, 11]
        self._fast_accept_conf = 0.78
        self._fast_accept_signal = 10.0
        self._fast_accept_text_len = 700

    def _paddle_runtime_available(self) -> bool:
        return (
            importlib.util.find_spec("paddleocr") is not None
            and importlib.util.find_spec("paddle") is not None
        )

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

    def _normalize_for_tesseract(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("OCR image is None")
        if len(image.shape) == 2:
            return image
        if image.shape[2] == 1:
            return image[:, :, 0]
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    def _build_variants(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        base_gray = self._normalize_for_tesseract(image)
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8)).apply(base_gray)

        _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(
            clahe,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )

        denoised = cv2.fastNlMeansDenoising(base_gray, None, h=7, templateWindowSize=7, searchWindowSize=21)
        sharpened = cv2.addWeighted(
            denoised,
            1.7,
            cv2.GaussianBlur(denoised, (0, 0), 1.2),
            -0.7,
            0,
        )

        return {
            "gray": base_gray,
            "clahe": clahe,
            "otsu": otsu,
            "adaptive": adaptive,
            "sharpened": sharpened,
        }

    def _ocr_signal_score(self, text: str) -> float:
        if not text:
            return 0.0

        lowered = text.lower()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        short_line_ratio = 0.0
        if lines:
            short_lines = sum(1 for line in lines if len(line.split()) <= 2)
            short_line_ratio = short_lines / len(lines)

        keyword_signals = [
            "invoice",
            "invoice no",
            "dated",
            "gstin",
            "total",
            "amount",
            "tax",
            "buyer",
            "consignee",
            "bank",
            "ack no",
            "irn",
        ]
        keyword_hits = sum(1 for marker in keyword_signals if marker in lowered)

        gst_hits = len(re.findall(REGEX_PATTERNS["gst"], text, re.IGNORECASE))
        date_hits = len(re.findall(REGEX_PATTERNS["date"], text, re.IGNORECASE))
        amount_hits = len(re.findall(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})", text))
        line_item_rows = len(re.findall(r"(?m)^\s*\d+\s+[A-Za-z]", text))
        structured_label_lines = sum(1 for line in lines if ":" in line and len(line.split()) >= 3)
        pipe_penalty = min(text.count("|"), 500) * 0.08

        return (
            (keyword_hits * 1.4)
            + (min(gst_hits, 3) * 2.2)
            + (min(date_hits, 6) * 0.8)
            + (min(amount_hits, 20) * 0.15)
            + (min(line_item_rows, 8) * 1.2)
            + (min(structured_label_lines, 25) * 0.35)
            - pipe_penalty
            - (short_line_ratio * 22.0)
        )

    def _compose_score(self, avg_conf: float, text_len: int, signal_score: float) -> float:
        # Weight OCR confidence first, then structured invoice signals and text completeness.
        return (avg_conf * 100.0) + (signal_score * 4.0) + (min(text_len, 4500) / 110.0)

    def _text_from_tesseract_data(self, data: Dict[str, Any]) -> str:
        line_map: Dict[tuple, list] = {}
        texts = data.get("text", [])
        confs = data.get("conf", [])
        pages = data.get("page_num", [])
        blocks = data.get("block_num", [])
        pars = data.get("par_num", [])
        lines = data.get("line_num", [])

        for idx in range(len(texts)):
            token = str(texts[idx]).strip()
            if not token:
                continue

            conf = -1.0
            try:
                conf = float(str(confs[idx]).strip())
            except (TypeError, ValueError, IndexError):
                conf = -1.0

            if conf >= 0 and conf < 15:
                continue

            key = (
                pages[idx] if idx < len(pages) else 0,
                blocks[idx] if idx < len(blocks) else 0,
                pars[idx] if idx < len(pars) else 0,
                lines[idx] if idx < len(lines) else idx,
            )
            line_map.setdefault(key, []).append(token)

        ordered_lines = [" ".join(words) for _, words in sorted(line_map.items(), key=lambda item: item[0])]
        return "\n".join(line for line in ordered_lines if line.strip())

    def _evaluate_tesseract_candidate(self, variant_name: str, variant_image: np.ndarray, psm: int) -> Dict[str, Any]:
        config = self._build_config(psm)
        data = pytesseract.image_to_data(variant_image, config=config, output_type=Output.DICT)
        text = self._text_from_tesseract_data(data)
        avg_conf = self._avg_confidence(data)
        text_len = len(text.strip())
        signal_score = self._ocr_signal_score(text)
        candidate_score = self._compose_score(avg_conf, text_len, signal_score)
        return {
            "variant": variant_name,
            "psm": psm,
            "data": data,
            "text": text,
            "avg_conf": avg_conf,
            "signal_score": signal_score,
            "score": candidate_score,
        }

    def _is_fast_accept(self, candidate: Dict[str, Any]) -> bool:
        return (
            candidate.get("avg_conf", 0.0) >= self._fast_accept_conf
            and candidate.get("signal_score", 0.0) >= self._fast_accept_signal
            and len(str(candidate.get("text", "")).strip()) >= self._fast_accept_text_len
        )

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
        """Tesseract OCR extraction with adaptive candidate evaluation."""
        variants = self._build_variants(image)
        best: Optional[Dict[str, Any]] = None

        def update_best(candidate: Dict[str, Any]):
            nonlocal best
            if best is None or candidate["score"] > best["score"]:
                best = candidate

        # Fast pass: often enough for clean invoices.
        primary = self._evaluate_tesseract_candidate("gray", variants["gray"], 6)
        update_best(primary)
        if self._is_fast_accept(primary):
            best = primary
        else:
            # Adaptive fallback: run a smaller shortlist first.
            shortlist = [
                ("clahe", 6),
                ("adaptive", 6),
                ("gray", 4),
                ("sharpened", 6),
            ]
            for variant_name, psm in shortlist:
                candidate = self._evaluate_tesseract_candidate(variant_name, variants[variant_name], psm)
                update_best(candidate)

            # Hard documents only: broaden search.
            hard_document = (
                (best or primary)["avg_conf"] < 0.60
                or (best or primary)["signal_score"] < 7.5
                or len(str((best or primary)["text"]).strip()) < 400
            )
            if hard_document:
                extended = [
                    ("otsu", 6),
                    ("clahe", 4),
                    ("adaptive", 4),
                    ("gray", 11),
                ]
                for variant_name, psm in extended:
                    candidate = self._evaluate_tesseract_candidate(variant_name, variants[variant_name], psm)
                    update_best(candidate)

        if best is None:
            raise RuntimeError("Tesseract OCR failed to produce any output")

        data = best["data"]
        text_boxes = []
        confidences = []

        for i in range(len(data.get("text", []))):
            word = str(data["text"][i]).strip()
            if not word:
                continue

            conf_raw = str(data["conf"][i]).strip()
            conf = float(conf_raw) if conf_raw else -1.0
            if conf >= 0:
                confidences.append(conf / 100)

            text_boxes.append(
                {
                    "text": word,
                    "confidence": conf / 100 if conf >= 0 else 0.0,
                    "bbox": {
                        "x": data["left"][i],
                        "y": data["top"][i],
                        "w": data["width"][i],
                        "h": data["height"][i],
                    },
                }
            )

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        logger.info(
            "Tesseract selected variant=%s psm=%s score=%.2f signal=%.2f conf=%.2f",
            best["variant"],
            best["psm"],
            best["score"],
            best["signal_score"],
            avg_confidence,
        )

        return {
            "text": best["text"],
            "boxes": text_boxes,
            "average_confidence": avg_confidence,
            "engine": "Tesseract",
            "variant": best["variant"],
            "psm": best["psm"],
        }
