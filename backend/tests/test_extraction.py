
import pytest
from unittest.mock import AsyncMock
import numpy as np
from backend.ai.vision_llm import VisionLLMEngine
from backend.services.processing_service import ProcessingService

# Sample extraction data for testing
SAMPLE_EXTRACTION_RESPONSE = {
    "invoice_number": "INV-2024-001",
    "invoice_date": "2024-01-15",
    "vendor_name": "Tech Solutions Inc.",
    "total_amount": 15000.00,
    "currency": "INR",
    "line_items": [
        {
            "description": "Server Maintenance",
            "quantity": 1,
            "unit_price": 10000.00,
            "total": 10000.00
        },
        {
            "description": "Software License",
            "quantity": 2,
            "unit_price": 2500.00,
            "total": 5000.00
        }
    ]
}

@pytest.fixture
def mock_image():
    """Create a dummy numpy image"""
    return np.zeros((100, 100, 3), dtype=np.uint8)

@pytest.fixture
def vision_llm_engine():
    """Fixture for VisionLLMEngine"""
    return VisionLLMEngine()

@pytest.fixture
def processing_service():
    """Fixture for ProcessingService with all dependencies mocked"""
    return ProcessingService(
        invoice_repo=AsyncMock(),
        preprocessing=AsyncMock(),
        ocr=AsyncMock(),
        layout_detection=AsyncMock(),
        vision_llm=AsyncMock(),
        ner=AsyncMock(),
        validation=AsyncMock()
    )

@pytest.mark.asyncio
async def test_heuristic_extraction_basic(vision_llm_engine):
    """Test heuristic extraction from OCR text"""
    ocr_text = """
    Invoice No: INV-2024-001
    Invoice Date: 15/01/2024
    Total: Rs. 15000.00
    GSTIN: 18AABCU9603R2Z5
    """
    result = await vision_llm_engine.extract_fields(
        image=np.zeros((10, 10, 3), dtype=np.uint8),
        ocr_text=ocr_text,
        layout_info={}
    )
    assert result["invoice_number"] == "INV-2024-001"
    assert result["invoice_date"] == "2024-01-15"
    assert result["total_amount"] == 15000.00
    assert result["vendor_gst"] == "18AABCU9603R2Z5"

@pytest.mark.asyncio
async def test_extract_fields_success(vision_llm_engine, mock_image):
    """Test the full extract_fields method with mocked API call"""
    result = await vision_llm_engine.extract_fields(
        image=mock_image,
        ocr_text="Invoice No: INV-2024-001\nTotal: 15000",
        layout_info={"tables": []}
    )
    
    assert result["invoice_number"] == "INV-2024-001"

@pytest.mark.asyncio
async def test_realistic_invoice_ocr_parsing(vision_llm_engine, mock_image):
    """Ensure heuristics parse noisy OCR text from scanned invoice PDFs."""
    ocr_text = """
    Tax Invoice Original e-Invoice
    Ack No. : 142518116670710
    Ack Date : 22-Aug-25
    Jay Ess Hydropower Co. Invoice No. Dated
    Kshetra Mandir Market, Near OBC, JSHP/25-26/1082 22-Aug-25
    GSTIN/UIN: O9AJQPB6361G1Z1
    Buyer (Bill to)
    Techno Electric & Engineering Co Ltd
    Mohanlalganj Near Radha Swami Satsang Bas, Lucknow
    GSTIN/UIN : O9AAJCS4400J1ZA
    1 Mcb 63amp DP 853650 1 Pcs 475.00 402.54 Pcs 402.54
    2 Steelgrip Tape 854690 3 Pcs 9.99 8.47 Pcs 25.41
    3 Air/Water Hose Pipe 40091100 2.00 Mtr 170.00 144.07 Mtr 288.14
    CGST 64.45
    SGST 64.45
    Total 845.00
    Bank Name : Axis Bank A/c 922030027678945
    A/c No. : 922030027678945
    """
    result = await vision_llm_engine.extract_fields(
        image=mock_image,
        ocr_text=ocr_text,
        layout_info={}
    )

    assert result["invoice_number"] == "JSHP/25-26/1082"
    assert result["invoice_date"] == "2025-08-22"
    assert result["vendor_name"] == "Jay Ess Hydropower Co"
    assert result["vendor_gst"] == "09AJQPB6361G1Z1"
    assert result["buyer_gst"] == "09AAJCS4400J1ZA"
    assert result["invoice_amount"] == 716.09
    assert result["tax_amount"] == 128.9
    assert result["total_amount"] == 845.0
    assert result["tax_rate"] is None or result["tax_rate"] > 0
    assert result["bank_details"]["account_number"] == "922030027678945"
    assert len(result["line_items"]) >= 3

@pytest.mark.asyncio
async def test_extraction_pipeline_flow(processing_service, mock_image):
    """
    Test the orchestration logic in ProcessingService.
    Ensures data flows from Step 1 (Preprocessing) to Step 6 (Validation).
    """
    # Setup mocks for each step
    processing_service.preprocessing.process_image.return_value = mock_image
    processing_service.ocr.extract_text.return_value = {"text": "OCR Data"}
    processing_service.layout_detection.detect_layout.return_value = {"tables": []}
    processing_service.vision_llm.extract_fields.return_value = SAMPLE_EXTRACTION_RESPONSE
    processing_service.ner.extract_entities.return_value = {"vendors": []}
    processing_service.validation.validate_extraction.return_value = (SAMPLE_EXTRACTION_RESPONSE, {"overall": 0.9})
    
    # Execute
    result = await processing_service.process_invoice(
        invoice_id="test-id",
        file_path="dummy/path.jpg"
    )
    
    # Assertions
    assert result["status"] == "completed"
    assert result["extracted_data"] == SAMPLE_EXTRACTION_RESPONSE
    assert result["confidence_scores"]["overall"] == 0.9
    
    # Verify call order (implicit by data flow, but we can check specific calls)
    processing_service.preprocessing.process_image.assert_called_once()
    processing_service.ocr.extract_text.assert_called_once()
    processing_service.vision_llm.extract_fields.assert_called_once()
    processing_service.invoice_repo.update.assert_called()  # Status updates


@pytest.mark.asyncio
async def test_extraction_pipeline_forwards_handwriting_preference(processing_service, mock_image):
    processing_service.preprocessing.process_image.return_value = mock_image
    processing_service.ocr.extract_text.return_value = {"text": "OCR Data"}
    processing_service.layout_detection.detect_layout.return_value = {"tables": []}
    processing_service.vision_llm.extract_fields.return_value = SAMPLE_EXTRACTION_RESPONSE
    processing_service.ner.extract_entities.return_value = {"vendors": []}
    processing_service.validation.validate_extraction.return_value = (SAMPLE_EXTRACTION_RESPONSE, {"overall": 0.9})

    await processing_service.process_invoice(
        invoice_id="test-id",
        file_path="dummy/path.jpg",
        prefer_handwriting_ocr=True,
    )

    processing_service.ocr.extract_text.assert_called_once_with(
        mock_image,
        prefer_handwriting_ocr=True,
    )

@pytest.mark.asyncio
async def test_extraction_failure_handling(processing_service):
    """Test that exceptions in the pipeline are caught and logged"""
    # Simulate a failure in OCR step
    processing_service.preprocessing.process_image.return_value = np.zeros((10,10))
    processing_service.ocr.extract_text.side_effect = Exception("OCR Engine Failed")
    
    with pytest.raises(Exception) as excinfo:
        await processing_service.process_invoice("test-id", "path.jpg")
    
    assert "OCR Engine Failed" in str(excinfo.value)
    
    # Verify status was updated to failed
    # We check the last call to invoice_repo.update
    call_args = processing_service.invoice_repo.update.call_args_list[-1]
    assert call_args[0][0] == "test-id"
    assert call_args[0][1]["processing_status"] == "failed"
    assert "OCR Engine Failed" in call_args[0][1]["error_message"]
