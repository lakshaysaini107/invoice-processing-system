import cv2
import numpy as np
from pathlib import Path
from backend.core.logging import logger

class PreprocessingEngine:
    """Enhance invoice images for better OCR accuracy"""

    def __init__(self):
        self.target_dpi = 300
        self.max_pdf_pages = 3

    async def process_image(self, file_path: str) -> np.ndarray:
        """
        Complete preprocessing pipeline:
        1. Load image
        2. Correct skew
        3. Denoise
        4. Enhance contrast
        5. Light sharpening
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

            # 4. Light sharpening keeps characters crisp without destroying details
            image = await self._sharpen(image)
            logger.info("Sharpening applied")
            
            return image
            
        except Exception as e:
            logger.error(f"Preprocessing error: {str(e)}")
            raise

    async def _load_image(self, file_path: str) -> np.ndarray:
        """Load image from file path. If PDF, render pages to image."""
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            return self._render_pdf_pages(file_path)
        return cv2.imread(file_path)

    def _render_pdf_pages(self, file_path: str) -> np.ndarray:
        """Render up to max_pdf_pages pages of a PDF to a single stacked BGR image."""
        try:
            import fitz  # PyMuPDF
        except Exception as e:
            raise RuntimeError(
                "PDF support requires PyMuPDF. Install with: pip install pymupdf"
            ) from e

        with fitz.open(file_path) as doc:
            if doc.page_count == 0:
                raise ValueError("PDF has no pages")

            scale = self.target_dpi / 72.0
            matrix = fitz.Matrix(scale, scale)
            rendered_pages = []

            page_count = min(doc.page_count, self.max_pdf_pages)
            for page_index in range(page_count):
                page = doc.load_page(page_index)
                pix = page.get_pixmap(matrix=matrix, alpha=False)

                img = np.frombuffer(pix.samples, dtype=np.uint8)
                img = img.reshape(pix.height, pix.width, pix.n)

                # Pixmap is RGB; convert to BGR for OpenCV consistency
                if pix.n >= 3:
                    img = img[:, :, :3]
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                rendered_pages.append(img)

            if not rendered_pages:
                raise ValueError("Failed to render PDF pages")

            if len(rendered_pages) == 1:
                return rendered_pages[0]

            max_width = max(page.shape[1] for page in rendered_pages)
            normalized_pages = []
            spacer_height = 40

            for page in rendered_pages:
                height, width = page.shape[:2]
                if width < max_width:
                    page = cv2.copyMakeBorder(
                        page,
                        top=0,
                        bottom=0,
                        left=0,
                        right=max_width - width,
                        borderType=cv2.BORDER_CONSTANT,
                        value=(255, 255, 255),
                    )
                normalized_pages.append(page)
                normalized_pages.append(
                    np.full((spacer_height, max_width, 3), 255, dtype=np.uint8)
                )

            # Drop the trailing spacer
            normalized_pages = normalized_pages[:-1]
            return np.vstack(normalized_pages)

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
        
        clahe = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Convert back to BGR
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return enhanced

    async def _sharpen(self, image: np.ndarray) -> np.ndarray:
        """Sharpen image while preserving edges for OCR."""
        # Unsharp mask directly on BGR image; avoids a second expensive denoise pass.
        blurred = cv2.GaussianBlur(image, (0, 0), 1.1)
        return cv2.addWeighted(image, 1.35, blurred, -0.35, 0)

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
