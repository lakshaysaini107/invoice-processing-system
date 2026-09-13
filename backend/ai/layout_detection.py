from typing import Any, Dict, List
import cv2
import numpy as np


class LayoutDetector:
    def detect_layout(self, image_np: np.ndarray) -> Dict[str, Any]:
        try:
            if len(image_np.shape) == 3:
                gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = image_np.copy()

            h, w = gray.shape
            # Detect horizontal and vertical lines for tables
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(w / 30), 1))
            detected_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            contours, _ = cv2.findContours(detected_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            tables = []
            for c in contours:
                x, y, cw, ch = cv2.boundingRect(c)
                if cw > w * 0.3:
                    tables.append({"bbox": [x, y, cw, ch], "type": "table_region"})

            sections = {
                "header": [0, 0, w, int(h * 0.25)],
                "body": [0, int(h * 0.25), w, int(h * 0.65)],
                "footer": [0, int(h * 0.90), w, int(h * 0.10)],
            }

            return {
                "document_dimensions": {"width": w, "height": h},
                "sections": sections,
                "tables_detected": len(tables),
                "table_regions": tables,
            }
        except Exception:
            return {
                "document_dimensions": {"width": 0, "height": 0},
                "sections": {},
                "tables_detected": 0,
                "table_regions": [],
            }


layout_detector = LayoutDetector()
