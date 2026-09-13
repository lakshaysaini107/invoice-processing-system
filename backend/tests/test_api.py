import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_upload_and_list_invoices(client):
    file_content = b"Dummy invoice content for test"
    files = {"file": ("test_invoice.pdf", file_content, "application/pdf")}
    response = await client.post("/api/invoices/upload", files=files)
    assert response.status_code == 200
    inv = response.json()
    assert inv["filename"] == "test_invoice.pdf"
    invoice_id = inv["id"]

    # List
    list_res = await client.get("/api/invoices/list")
    assert list_res.status_code == 200
    inv_list = list_res.json()
    assert len(inv_list) > 0

    # Start process
    proc_res = await client.post("/api/process/start", json={"invoice_id": invoice_id})
    assert proc_res.status_code == 200
