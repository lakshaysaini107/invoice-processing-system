from typing import Any, Dict, Optional
import numpy as np
from backend.app.config import settings
from backend.core.logging import logger


class HandwritingOCR:
    def __init__(self):
        self.enabled = settings.ENABLE_TROCR_HANDWRITING

    def process_handwriting(self, image_np: np.ndarray) -> Optional[str]:
        if not self.enabled:
            return None
        logger.info("TrOCR handwriting processing requested.")
        return None


handwriting_ocr = HandwritingOCR()
