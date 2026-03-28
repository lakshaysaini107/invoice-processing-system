import pytest
import numpy as np
from backend.ai.ocr_engine import OCREngine

@pytest.fixture
def ocr_engine():
    return OCREngine(use_paddle=False)  # Use Tesseract for testing

def test_should_skip_handwriting_for_strong_base_ocr(ocr_engine):
    base_result = {
        "text": "Invoice No: INV-2026-001\nInvoice Date: 28/03/2026\nGSTIN: 29ABCDE1234F1Z5\nTotal Amount: 1250.00",
        "average_confidence": 0.91,
        "engine": "Tesseract",
    }

    assert ocr_engine._should_try_handwriting_result(base_result) is False


def test_should_try_handwriting_for_low_confidence_ocr(ocr_engine):
    base_result = {
        "text": "inv no maybe\nsmudged total",
        "average_confidence": 0.24,
        "engine": "Tesseract",
    }

    assert ocr_engine._should_try_handwriting_result(base_result) is True


def test_should_promote_handwriting_when_it_scores_better(ocr_engine):
    base_result = {
        "text": "smudged inv total",
        "average_confidence": 0.25,
        "engine": "Tesseract",
    }
    handwriting_result = {
        "text": "Invoice No: H-17\nInvoice Date: 28/03/2026\nTotal: 985.00",
        "average_confidence": 0.73,
        "engine": "TrOCR",
    }

    assert ocr_engine._should_promote_handwriting_result(base_result, handwriting_result) is True


def test_should_keep_base_when_handwriting_is_not_clear_improvement(ocr_engine):
    base_result = {
        "text": "Invoice No: INV-11\nTotal: 985.00",
        "average_confidence": 0.62,
        "engine": "Tesseract",
    }
    handwriting_result = {
        "text": "maybe invoice maybe total",
        "average_confidence": 0.49,
        "engine": "TrOCR",
    }

    assert ocr_engine._should_promote_handwriting_result(base_result, handwriting_result) is False


class _StubHandwritingEngine:
    enabled = True

    async def extract_text(self, image):
        return {
            "text": "Invoice No: HW-101\nInvoice Date: 28/03/2026\nTotal: 455.00",
            "boxes": [],
            "average_confidence": 0.81,
            "engine": "TrOCR",
        }

    def is_available(self, force: bool = False):
        return True


@pytest.mark.asyncio
async def test_extract_text_uses_handwriting_fallback_only_when_better(ocr_engine, monkeypatch):
    ocr_engine.handwriting_ocr = _StubHandwritingEngine()

    async def fake_base_ocr(_image):
        return {
            "text": "inv no\n455",
            "boxes": [],
            "average_confidence": 0.18,
            "engine": "Tesseract",
        }

    monkeypatch.setattr(ocr_engine, "_tesseract_ocr", fake_base_ocr)

    image = np.ones((120, 320, 3), dtype=np.uint8) * 255
    result = await ocr_engine.extract_text(image)

    assert result["engine"] == "TrOCR"
    assert result["fallback_from"] == "Tesseract"
