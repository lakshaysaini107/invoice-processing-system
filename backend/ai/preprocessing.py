import cv2
import numpy as np
from pathlib import Path
from backend.core.logging import logger

class PreprocessingEngine:
    """Enhance invoice images for better OCR accuracy"""

    def __init__(self):
        self.target_dpi = 300

    async def process_image(self, file_path: str) -> np.ndarray:
        """
        Complete preprocessing pipeline:
        1. Load image
        2. Correct skew
        3. Denoise
        4. Enhance contrast
        5. Binarization
        """
        try:
            # Load image (supports PDF -> image conversion)
            image = await self._load_image(file_path)
            if image is None:
                raise ValueError(f"Failed to load image: {file_path}")
            
            logger.info(f"Image loaded: {image.shape}")
            
            # Convert to RGB if necessary
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            
            # 1. Skew correction
            image = await self._correct_skew(image)
            logger.info("Skew correction applied")
            
            # 2. Denoising
            image = await self._denoise(image)
            logger.info("Denoising applied")
            
            # 3. Contrast enhancement
            image = await self._enhance_contrast(image)
            logger.info("Contrast enhancement applied")
            
            # 4. Binarization for OCR
            image = await self._binarize(image)
            logger.info("Binarization applied")
            
            # 5. Deskew again if needed
            image = await self._correct_skew(image)
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}")
            raise

    async def _load_image(self, file_path: str) -> np.ndarray:
        """Load image from file path. If PDF, render first page to image."""
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            return self._render_pdf_first_page(file_path)
        return cv2.imread(file_path)

    def _render_pdf_first_page(self, file_path: str) -> np.ndarray:
        """Render the first page of a PDF to a BGR image array."""
        try:
            import fitz  # PyMuPDF
        except Exception as e:
            raise RuntimeError(
                "PDF support requires PyMuPDF. Install with: pip install pymupdf"
            ) from e

        with fitz.open(file_path) as doc:
            if doc.page_count == 0:
                raise ValueError("PDF has no pages")

            page = doc.load_page(0)
            scale = self.target_dpi / 72.0
            matrix = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            img = np.frombuffer(pix.samples, dtype=np.uint8)
            img = img.reshape(pix.height, pix.width, pix.n)

            # Pixmap is RGB; convert to BGR for OpenCV consistency
            if pix.n >= 3:
                img = img[:, :, :3]
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

            return img

    async def _correct_skew(self, image: np.ndarray) -> np.ndarray:
        """Correct document skew using contours"""
        try:
            if len(image.shape) == 2:
                gray = image
            elif image.shape[2] == 1:
                gray = image[:, :, 0]
            else:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
            if lines is None:
                return image
            
            angles = []
            for line in lines:
                rho, theta = line[0]
                angle = (theta * 180 / np.pi) - 90
                if -30 < angle < 30:
                    angles.append(angle)
            
            if angles:
                median_angle = np.median(angles)
                h, w = image.shape[:2]
                center = (w // 2, h // 2)
                
                rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                image = cv2.warpAffine(image, rotation_matrix, (w, h), 
                                     borderMode=cv2.BORDER_REFLECT)
            
            return image
        except Exception as e:
            logger.warning(f"Skew correction failed: {str(e)}")
            return image

    async def _denoise(self, image: np.ndarray) -> np.ndarray:
        """Remove noise from image"""
        # Bilateral filter preserves edges while reducing noise
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        return denoised

    async def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast using CLAHE"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return enhanced

    async def _binarize(self, image: np.ndarray) -> np.ndarray:
        """Convert to binary image for OCR"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Adaptive thresholding works better than global thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            11, 2
        )
        
        return binary
