import io
from typing import List, Tuple
import cv2
import fitz  # PyMuPDF
import numpy as np
from PIL import Image
from backend.core.logging import logger


class ImagePreprocessor:
    def convert_pdf_to_images(self, file_path: str, dpi: int = 200) -> List[np.ndarray]:
        images = []
        try:
            doc = fitz.open(file_path)
            for page in doc:
                pix = page.get_pixmap(dpi=dpi)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                images.append(np.array(img))
            doc.close()
        except Exception as exc:
            logger.error(f"Error converting PDF {file_path}: {exc}")
        return images

    def enhance_image(self, image_np: np.ndarray) -> np.ndarray:
        try:
            if len(image_np.shape) == 3 and image_np.shape[2] == 3:
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_np.copy()

            # CLAHE Contrast Enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Denoising
            denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

            # Convert back to 3-channel RGB for OCR engines
            return cv2.cvtColor(denoised, cv2.COLOR_GRAY2RGB)
        except Exception as exc:
            logger.warning(f"Image enhancement error: {exc}. Returning original.")
            return image_np


preprocessor = ImagePreprocessor()
