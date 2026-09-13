import numpy as np
from backend.ai.ocr_engine import ocr_engine


def test_ocr_engine_fallback():
    # Create blank test image numpy array
    dummy_img = np.ones((200, 400, 3), dtype=np.uint8) * 255
    res = ocr_engine.extract_text(dummy_img)
    assert isinstance(res, dict)
    assert "full_text" in res
    assert "lines" in res
    assert "engine" in res
