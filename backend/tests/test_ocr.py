import pytest
import numpy as np
from backend.ai.ocr_engine import OCREngine

@pytest.fixture
def ocr_engine():
    return OCREngine(use_paddle=False)  # Use Tesseract for testing

@pytest.mark.asyncio
async def test_ocr_extraction(ocr_engine, tmp_path):
    """Test OCR text extraction"""
    # Create a simple test image with text
    # This is a simplified test - in real tests, use proper invoice images
    image = np.ones((100, 300, 3), dtype=np.uint8) * 255
    
    # Save image
    test_image_path = tmp_path / "test.jpg"
    import cv2
    cv2.imwrite(str(test_image_path), image)
    
    # Note: This test will fail without actual text in the image
    # Use real invoice samples for actual testing
