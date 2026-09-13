import pytest


@pytest.mark.asyncio
async def test_erp_handoff_and_save(client):
    # Create invoice first
    file_content = b"Dummy invoice content for ERP test"
    files = {"file": ("erp_invoice.png", file_content, "image/png")}
    response = await client.post("/api/invoices/upload", files=files)
    assert response.status_code == 200
    inv = response.json()
    invoice_id = inv["id"]

    # ERP get invoice
    erp_res = await client.get(f"/api/erp/invoice/{invoice_id}")
    assert erp_res.status_code == 200
    erp_payload = erp_res.json()
    assert erp_payload["source_invoice_id"] == invoice_id

    # Save ERP record
    save_payload = {
        "source_invoice_id": invoice_id,
        "data": {
            "invoice_number": "ERP-12345",
            "vendor_name": "ACME Vendor",
            "total_amount": 10000.0,
        },
    }
    save_res = await client.post("/api/erp/save_erp", json=save_payload)
    assert save_res.status_code == 200
    save_data = save_res.json()
    assert "erp_record" in save_data
