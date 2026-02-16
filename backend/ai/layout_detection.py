import cv2
import numpy as np
from typing import Dict, Any, List
from backend.core.logging import logger

class LayoutDetectionEngine:
    """Detect tables, paragraphs, and document structure"""

    def __init__(self):
        self.table_threshold = 10
        self.min_table_size = (3, 3) # minimum 3x3 cells

    async def detect_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """Detect document structure: tables, paragraphs, sections"""
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Detect tables
            tables = await self._detect_tables(gray)
            
            # Detect text regions
            text_regions = await self._detect_text_regions(gray)
            
            # Detect sections/paragraphs
            sections = await self._detect_sections(gray)
            
            layout_info = {
                "tables": tables,
                "text_regions": text_regions,
                "sections": sections,
                "document_width": image.shape[1],
                "document_height": image.shape[0]
            }
            
            logger.info(f"Layout detected: {len(tables)} tables, {len(text_regions)} text regions")
            
            return layout_info
            
        except Exception as e:
            logger.error(f"Layout detection error: {str(e)}")
            raise

    async def _detect_tables(self, gray: np.ndarray) -> List[Dict[str, Any]]:
        """Detect table structures using morphological operations"""
        # Create binary image
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        
        # Invert
        inverted = cv2.bitwise_not(binary)
        
        # Detect horizontal lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, horizontal_kernel)
        
        # Detect vertical lines
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        vertical_lines = cv2.morphologyEx(inverted, cv2.MORPH_OPEN, vertical_kernel)
        
        # Combine
        grid = cv2.add(horizontal_lines, vertical_lines)
        
        # Find contours
        contours, _ = cv2.findContours(grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        tables = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 100 and h > 50: # Minimum table size
                tables.append({
                    "bbox": {"x": x, "y": y, "width": w, "height": h},
                    "type": "table",
                    "rows": 0, # Can be refined with advanced analysis
                    "cols": 0
                })
        
        return tables

    async def _detect_text_regions(self, gray: np.ndarray) -> List[Dict[str, Any]]:
        """Detect text regions/blocks"""
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 30 and h > 15: # Minimum text block size
                text_regions.append({
                    "bbox": {"x": x, "y": y, "width": w, "height": h},
                    "type": "text_block"
                })
        
        return text_regions

    async def _detect_sections(self, gray: np.ndarray) -> List[Dict[str, Any]]:
        """Detect document sections (header, body, footer)"""
        h = gray.shape[0]
        third = h // 3
        
        sections = [
            {"name": "header", "y_start": 0, "y_end": third},
            {"name": "body", "y_start": third, "y_end": 2 * third},
            {"name": "footer", "y_start": 2 * third, "y_end": h}
        ]
        
        return sections
