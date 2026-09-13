from backend.ai.vision_llm import vision_llm_extractor


def test_heuristic_field_extraction():
    sample_ocr = {
        "full_text": """
        ACME Supplies Pvt Ltd
        GSTIN: 27AAAAA0000A1Z5
        INVOICE NO: INV-2026-001
        Date: 12/09/2026
        Bill To: TechCorp India
        GSTIN: 29BBBCC1111B1Z2
        Total Amount: ₹ 15,500.00
        Subtotal: ₹ 14,000.00
        Tax: ₹ 1,500.00
        Account No: 9876543210
        IFSC: HDFC0001234
        """,
        "lines": [],
    }

    extracted = vision_llm_extractor.extract_fields(sample_ocr)
    assert extracted["invoice_number"] == "INV-2026-001"
    assert extracted["vendor_gst"] == "27AAAAA0000A1Z5"
    assert extracted["buyer_gst"] == "29BBBCC1111B1Z2"
    assert extracted["total_amount"] == 15500.0
    assert extracted["invoice_amount"] == 14000.0
    assert extracted["tax_amount"] == 1500.0
    assert extracted["bank_details"]["account_number"] == "9876543210"
    assert extracted["bank_details"]["ifsc"] == "HDFC0001234"
