import pytest
from backend.services.validation_service import ValidationService

@pytest.fixture
def validation_service():
    return ValidationService()

@pytest.mark.asyncio
async def test_validate_invoice_number(validation_service):
    """Test invoice number validation"""
    is_valid, confidence, value = await validation_service._validate_invoice_number(
        "INV-2024-001", "Invoice Number: INV-2024-001"
    )
    assert is_valid
    assert confidence > 0.5

@pytest.mark.asyncio
async def test_validate_gst(validation_service):
    """Test GST validation"""
    is_valid, confidence, value = await validation_service._validate_gst(
        "18AABCU9603R2Z5", "GSTIN: 18AABCU9603R2Z5"
    )
    assert is_valid
    assert confidence >= 0.95

@pytest.mark.asyncio
async def test_validate_date(validation_service):
    """Test date validation"""
    is_valid, confidence, value = await validation_service._validate_date(
        "2024-01-15", "Date: 2024-01-15"
    )
    assert is_valid
    assert confidence >= 0.95

@pytest.mark.asyncio
async def test_validate_amount(validation_service):
    """Test amount validation"""
    is_valid, confidence, value = await validation_service._validate_amount(
        "10000.50", "Amount: ₹10,000.50"
    )
    assert is_valid
    assert value == 10000.50
