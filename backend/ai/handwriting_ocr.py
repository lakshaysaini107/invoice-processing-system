import importlib.util
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PIL import Image

from backend.app.config import settings
from backend.core.logging import logger


class HandwritingOCREngine:
    """Optional TrOCR-based line recognizer for simple handwritten documents."""

    def __init__(self):
        self.enabled = bool(getattr(settings, "ENABLE_TROCR_HANDWRITING", False))
        self.model_name = str(getattr(settings, "TROCR_MODEL_NAME", "microsoft/trocr-small-handwritten"))
        self.device_preference = str(getattr(settings, "TROCR_DEVICE", "cpu")).strip().lower() or "cpu"
        self.max_regions = max(1, int(getattr(settings, "TROCR_MAX_REGIONS", 24)))
        self.min_line_height = max(8, int(getattr(settings, "TROCR_MIN_LINE_HEIGHT", 18)))
        self._processor = None
        self._model = None
        self._torch = None
        self._device = "cpu"
        self._missing_runtime_logged = False
        self._load_error: Optional[str] = None

    def is_available(self, force: bool = False) -> bool:
        if not (self.enabled or force):
            return False

        if self._model is not None and self._processor is not None and self._torch is not None:
            return True

        if not self._runtime_available():
            if not self._missing_runtime_logged:
                logger.warning(
                    "TrOCR handwriting support is enabled but optional dependencies are missing. "
                    "Install backend/requirements-handwriting.txt to activate it."
                )
                self._missing_runtime_logged = True
            return False

        try:
            self._ensure_loaded()
            return True
        except Exception as exc:
            self._load_error = str(exc)
            logger.warning("TrOCR handwriting model could not be loaded: %s", self._load_error)
            return False

    def _runtime_available(self) -> bool:
        required_modules = ("torch", "transformers", "sentencepiece")
        return all(importlib.util.find_spec(module_name) is not None for module_name in required_modules)

    def _ensure_loaded(self):
        if self._model is not None and self._processor is not None and self._torch is not None:
            return

        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        self._torch = torch
        self._device = self._resolve_device(torch)
        self._processor = TrOCRProcessor.from_pretrained(self.model_name)
        self._model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
        self._model.to(self._device)
        self._model.eval()
        logger.info("TrOCR handwriting OCR loaded: model=%s device=%s", self.model_name, self._device)

    def _resolve_device(self, torch_module) -> str:
        preference = self.device_preference
        if preference == "auto":
            return "cuda" if torch_module.cuda.is_available() else "cpu"
        if preference == "cuda" and not torch_module.cuda.is_available():
            logger.warning("TrOCR requested CUDA, but no CUDA device is available. Falling back to CPU.")
            return "cpu"
        return preference or "cpu"

    async def extract_text(self, image: np.ndarray) -> Dict[str, Any]:
        if not self.is_available(force=True):
            raise RuntimeError("TrOCR handwriting OCR is not available.")

        color_image = self._normalize_color_image(image)
        regions = self._detect_line_regions(color_image)
        boxes: List[Dict[str, Any]] = []
        text_lines: List[str] = []
        confidences: List[float] = []

        for bbox in regions[: self.max_regions]:
            crop = self._crop_region(color_image, bbox)
            text, confidence = self._recognize_region(crop)
            cleaned = text.strip()
            if not cleaned:
                continue

            text_lines.append(cleaned)
            confidences.append(confidence)
            boxes.append(
                {
                    "text": cleaned,
                    "confidence": confidence,
                    "bbox": {
                        "x": bbox["x"],
                        "y": bbox["y"],
                        "w": bbox["w"],
                        "h": bbox["h"],
                    },
                }
            )

        if not text_lines:
            full_text, full_confidence = self._recognize_region(color_image)
            cleaned = full_text.strip()
            if cleaned:
                text_lines.append(cleaned)
                confidences.append(full_confidence)
                boxes.append(
                    {
                        "text": cleaned,
                        "confidence": full_confidence,
                        "bbox": {"x": 0, "y": 0, "w": int(color_image.shape[1]), "h": int(color_image.shape[0])},
                    }
                )

        average_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return {
            "text": "\n".join(text_lines).strip(),
            "boxes": boxes,
            "average_confidence": average_confidence,
            "engine": "TrOCR",
            "regions": len(boxes),
        }

    def _normalize_color_image(self, image: np.ndarray) -> np.ndarray:
        if image is None:
            raise ValueError("Handwriting OCR image is None")
        if len(image.shape) == 2:
            return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        if image.shape[2] == 4:
            return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
        return image.copy()

    def _detect_line_regions(self, image: np.ndarray) -> List[Dict[str, int]]:
        height, width = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            31,
            15,
        )
        binary = cv2.medianBlur(binary, 3)

        kernel_width = max(25, width // 20)
        kernel_height = max(1, height // 300)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, kernel_height))
        connected = cv2.dilate(binary, kernel, iterations=1)

        contours, _ = cv2.findContours(connected, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions: List[Dict[str, int]] = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w < max(60, width // 14):
                continue
            if h < self.min_line_height or h > max(self.min_line_height * 6, height // 4):
                continue
            if w * h < max(600, (width * height) // 700):
                continue
            if w / max(h, 1) < 2.2:
                continue

            pad_x = max(8, w // 40)
            pad_y = max(6, h // 3)
            x0 = max(0, x - pad_x)
            y0 = max(0, y - pad_y)
            x1 = min(width, x + w + pad_x)
            y1 = min(height, y + h + pad_y)
            regions.append({"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0})

        regions.sort(key=lambda item: (item["y"], item["x"]))
        merged = self._merge_regions(regions)
        if merged:
            return merged[: self.max_regions]

        return [{"x": 0, "y": 0, "w": width, "h": height}]

    def _merge_regions(self, regions: List[Dict[str, int]]) -> List[Dict[str, int]]:
        if not regions:
            return []

        merged = [regions[0].copy()]
        for region in regions[1:]:
            current = merged[-1]
            current_mid = current["y"] + (current["h"] // 2)
            region_mid = region["y"] + (region["h"] // 2)
            same_row = abs(current_mid - region_mid) <= max(current["h"], region["h"])
            touching = region["x"] <= current["x"] + current["w"] + 24

            if same_row and touching:
                x0 = min(current["x"], region["x"])
                y0 = min(current["y"], region["y"])
                x1 = max(current["x"] + current["w"], region["x"] + region["w"])
                y1 = max(current["y"] + current["h"], region["y"] + region["h"])
                merged[-1] = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
            else:
                merged.append(region.copy())

        return merged

    def _crop_region(self, image: np.ndarray, bbox: Dict[str, int]) -> np.ndarray:
        x0 = bbox["x"]
        y0 = bbox["y"]
        x1 = x0 + bbox["w"]
        y1 = y0 + bbox["h"]
        return image[y0:y1, x0:x1]

    def _recognize_region(self, image: np.ndarray) -> tuple[str, float]:
        self._ensure_loaded()
        pil_image = self._prepare_region_image(image)
        pixel_values = self._processor(images=pil_image, return_tensors="pt").pixel_values.to(self._device)

        with self._torch.inference_mode():
            generated = self._model.generate(
                pixel_values,
                max_new_tokens=64,
                return_dict_in_generate=True,
                output_scores=True,
            )

        text = self._processor.batch_decode(generated.sequences, skip_special_tokens=True)[0]
        confidence = self._sequence_confidence(generated)
        return text, confidence

    def _prepare_region_image(self, image: np.ndarray) -> Image.Image:
        if len(image.shape) == 2:
            gray = image
        else:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        normalized = cv2.fastNlMeansDenoising(gray, None, h=5, templateWindowSize=7, searchWindowSize=21)
        bordered = cv2.copyMakeBorder(normalized, 8, 8, 10, 10, cv2.BORDER_CONSTANT, value=255)
        rgb = cv2.cvtColor(bordered, cv2.COLOR_GRAY2RGB)
        return Image.fromarray(rgb)

    def _sequence_confidence(self, generated) -> float:
        scores = list(getattr(generated, "scores", []) or [])
        sequences = getattr(generated, "sequences", None)
        if not scores or sequences is None:
            return 0.0

        token_ids = sequences[0, -len(scores):]
        confidences = []
        for step_scores, token_id in zip(scores, token_ids):
            probabilities = self._torch.nn.functional.softmax(step_scores[0], dim=-1)
            confidences.append(float(probabilities[int(token_id)].item()))

        return sum(confidences) / len(confidences) if confidences else 0.0
