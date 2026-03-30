from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.api import auth, upload
from backend.app import dependencies
from backend.app.main import app
from backend.database.mysql import MySQLClient


class InMemoryUserRepository:
    def __init__(self):
        self._users_by_id: Dict[str, Dict[str, Any]] = {}
        self._users_by_email: Dict[str, Dict[str, Any]] = {}

    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(user_data.get("_id") or uuid4().hex)
        created_at = user_data.get("created_at") or datetime.utcnow()
        user = {
            "_id": user_id,
            "email": str(user_data["email"]),
            "password_hash": user_data["password_hash"],
            "full_name": user_data["full_name"],
            "company": user_data.get("company"),
            "role": user_data.get("role", "user"),
            "created_at": created_at,
            "is_active": bool(user_data.get("is_active", True)),
        }
        self._users_by_id[user_id] = user
        self._users_by_email[user["email"]] = user
        return user

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self._users_by_email.get(str(email))

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self._users_by_id.get(str(user_id))


class InMemoryInvoiceRepository:
    def __init__(self):
        self._invoices: Dict[str, Dict[str, Any]] = {}

    async def create(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        record = dict(invoice_data)
        record.setdefault("upload_time", datetime.utcnow())
        self._invoices[record["invoice_id"]] = record
        return record

    async def get_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        return self._invoices.get(invoice_id)

    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ):
        rows = [
            row
            for row in self._invoices.values()
            if str(row.get("user_id")) == str(user_id)
        ]
        if status:
            rows = [row for row in rows if row.get("processing_status") == status]
        rows.sort(key=lambda row: row.get("upload_time") or datetime.min, reverse=True)
        return rows[skip : skip + limit]

    async def list_recent(
        self,
        skip: int = 0,
        limit: int = 50,
    ):
        rows = list(self._invoices.values())
        rows.sort(key=lambda row: row.get("upload_time") or datetime.min, reverse=True)
        return rows[skip : skip + limit]

    async def delete(self, invoice_id: str) -> bool:
        if invoice_id not in self._invoices:
            raise ValueError(f"Invoice not found: {invoice_id}")
        del self._invoices[invoice_id]
        return True


class InMemoryUploadService:
    async def validate_file(self, file) -> bool:
        return True

    async def save_file(self, file, invoice_id: str, user_id: str) -> str:
        return f"mock/{user_id}/{invoice_id}"

    async def get_file_info(self, file_path: str) -> Dict[str, Any]:
        return {"size": 1024}

    async def delete_file(self, file_path: str) -> bool:
        return True


@dataclass
class TestContext:
    user_repo: InMemoryUserRepository
    invoice_repo: InMemoryInvoiceRepository
    upload_service: InMemoryUploadService


@pytest.fixture
def test_context() -> TestContext:
    return TestContext(
        user_repo=InMemoryUserRepository(),
        invoice_repo=InMemoryInvoiceRepository(),
        upload_service=InMemoryUploadService(),
    )


@pytest.fixture
def test_user_data() -> Dict[str, str]:
    return {
        "email": "tester@example.com",
        "password": "StrongPass123",
        "full_name": "Test User",
        "company": "Acme Corp",
    }


@pytest_asyncio.fixture
async def async_client(
    monkeypatch: pytest.MonkeyPatch,
    test_context: TestContext,
):
    async def _noop_connect(cls):
        return None

    async def _noop_close(cls):
        return None

    monkeypatch.setattr(MySQLClient, "connect_mysql", classmethod(_noop_connect))
    monkeypatch.setattr(MySQLClient, "close_mysql", classmethod(_noop_close))
    monkeypatch.setattr(dependencies.settings, "AUTH_DISABLED", False)

    # get_current_user resolves repositories directly from this module.
    monkeypatch.setattr(
        dependencies,
        "get_user_repository",
        lambda: test_context.user_repo,
    )
    monkeypatch.setattr(auth, "hash_password", lambda password: f"hashed::{password}")
    monkeypatch.setattr(
        auth,
        "verify_password",
        lambda plain_password, hashed_password: hashed_password == f"hashed::{plain_password}",
    )

    app.dependency_overrides[dependencies.get_user_repository] = lambda: test_context.user_repo
    app.dependency_overrides[auth.get_user_repository] = lambda: test_context.user_repo
    app.dependency_overrides[upload.get_invoice_repository] = lambda: test_context.invoice_repo
    app.dependency_overrides[upload.get_upload_service] = lambda: test_context.upload_service

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://localhost",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authenticated_client(
    async_client: AsyncClient,
    test_user_data: Dict[str, str],
) -> AsyncClient:
    await async_client.post("/api/auth/register", json=test_user_data)
    login_response = await async_client.post(
        "/api/auth/login",
        json={
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        },
    )
    token = login_response.json()["access_token"]
    async_client.headers["Authorization"] = f"Bearer {token}"
    return async_client
