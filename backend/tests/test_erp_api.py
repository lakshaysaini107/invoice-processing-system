import pytest
from datetime import datetime, timedelta

from backend.api import erp
from backend.app.dependencies import get_erp_current_invoice_store, get_erp_invoice_repository
from backend.app.main import app


class StubERPInvoiceRepository:
    def __init__(self):
        self.saved_requests = []

    async def save(self, source_invoice_id, data):
        self.saved_requests.append(
            {
                "source_invoice_id": source_invoice_id,
                "data": data,
            }
        )
        return {
            "id": 42,
            "source_invoice_id": source_invoice_id,
            "saved_at": "2026-03-25T10:00:00",
        }


@pytest.mark.asyncio
async def test_set_current_invoice_uses_selected_invoice(async_client, test_context):
    test_context.invoice_repo._invoices["inv-1"] = {
        "invoice_id": "inv-1",
        "user_id": "public",
        "filename": "invoice.pdf",
        "processing_status": "reviewed",
        "review_status": "approved",
        "extracted_data": {
            "invoice_number": "INV-1",
            "vendor_name": "Vendor One",
            "bank_details": {"account_number": "12345"},
        },
    }
    current_store = {}

    app.dependency_overrides[erp.get_invoice_repository] = lambda: test_context.invoice_repo
    app.dependency_overrides[get_erp_current_invoice_store] = lambda: current_store
    try:
        response = await async_client.post("/api/erp/set_current_invoice", json={"invoice_id": "inv-1"})
    finally:
        app.dependency_overrides.pop(erp.get_invoice_repository, None)
        app.dependency_overrides.pop(get_erp_current_invoice_store, None)

    assert response.status_code == 200
    assert current_store["source_invoice_id"] == "inv-1"
    assert current_store["invoice_number"] == "INV-1"


@pytest.mark.asyncio
async def test_get_current_invoice_returns_handoff_payload(async_client):
    current_store = {
        "source_invoice_id": "inv-2",
        "invoice_number": "INV-2",
        "vendor_name": "Vendor Two",
    }

    app.dependency_overrides[get_erp_current_invoice_store] = lambda: current_store
    try:
        response = await async_client.get("/api/erp/get_current_invoice")
    finally:
        app.dependency_overrides.pop(get_erp_current_invoice_store, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_invoice_id"] == "inv-2"
    assert payload["vendor_name"] == "Vendor Two"


@pytest.mark.asyncio
async def test_set_current_invoice_without_auth_uses_latest_eligible_invoice(async_client, test_context):
    test_context.invoice_repo._invoices["inv-old"] = {
        "invoice_id": "inv-old",
        "user_id": "user-a",
        "filename": "old.pdf",
        "upload_time": datetime.utcnow() - timedelta(hours=1),
        "processing_status": "reviewed",
        "review_status": "approved",
        "extracted_data": {
            "invoice_number": "INV-OLD",
            "vendor_name": "Older Vendor",
            "bank_details": {"account_number": "1111"},
        },
    }
    test_context.invoice_repo._invoices["inv-new"] = {
        "invoice_id": "inv-new",
        "user_id": "user-b",
        "filename": "new.pdf",
        "upload_time": datetime.utcnow(),
        "processing_status": "reviewed",
        "review_status": "approved",
        "extracted_data": {
            "invoice_number": "INV-NEW",
            "vendor_name": "Newest Vendor",
            "bank_details": {"account_number": "2222"},
        },
    }
    current_store = {}

    app.dependency_overrides[erp.get_invoice_repository] = lambda: test_context.invoice_repo
    app.dependency_overrides[get_erp_current_invoice_store] = lambda: current_store
    try:
        response = await async_client.post("/api/erp/set_current_invoice", json={})
    finally:
        app.dependency_overrides.pop(erp.get_invoice_repository, None)
        app.dependency_overrides.pop(get_erp_current_invoice_store, None)

    assert response.status_code == 200
    assert current_store["source_invoice_id"] == "inv-new"
    assert current_store["invoice_number"] == "INV-NEW"


@pytest.mark.asyncio
async def test_get_invoice_for_erp_returns_selected_invoice(async_client, test_context):
    test_context.invoice_repo._invoices["inv-erp"] = {
        "invoice_id": "inv-erp",
        "user_id": "public",
        "filename": "invoice-erp.pdf",
        "processing_status": "reviewed",
        "review_status": "approved",
        "extracted_data": {
            "invoice_number": "INV-ERP",
            "vendor_name": "ERP Vendor",
            "line_items": [],
            "bank_details": {"account_number": "123456789"},
        },
    }

    app.dependency_overrides[erp.get_invoice_repository] = lambda: test_context.invoice_repo
    try:
        response = await async_client.get("/api/erp/invoice/inv-erp")
    finally:
        app.dependency_overrides.pop(erp.get_invoice_repository, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_invoice_id"] == "inv-erp"
    assert payload["invoice_number"] == "INV-ERP"
    assert payload["vendor_name"] == "ERP Vendor"


@pytest.mark.asyncio
async def test_save_erp_persists_payload(async_client):
    repo = StubERPInvoiceRepository()
    app.dependency_overrides[get_erp_invoice_repository] = lambda: repo
    try:
        response = await async_client.post(
            "/api/erp/save_erp",
            json={
                "source_invoice_id": "inv-3",
                "data": {
                    "invoice_number": "INV-3",
                    "vendor_name": "Vendor Three",
                    "bank_details": {
                        "account_number": "9999",
                        "account_holder": "Vendor Three",
                        "bank_name": "Demo Bank",
                        "ifsc": "DEMO0001234",
                        "branch": "Main",
                    },
                },
            },
        )
    finally:
        app.dependency_overrides.pop(get_erp_invoice_repository, None)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "saved"
    assert repo.saved_requests[0]["source_invoice_id"] == "inv-3"
    assert repo.saved_requests[0]["data"]["invoice_number"] == "INV-3"
