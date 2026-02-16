import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class _LocalStore:
    """Simple JSON-backed store for local dev without MongoDB."""

    _data: Optional[Dict[str, List[Dict[str, Any]]]] = None
    _path = Path(__file__).resolve().parents[3] / "data" / "local_db.json"

    @classmethod
    def _ensure_loaded(cls) -> None:
        if cls._data is not None:
            return
        if cls._path.exists():
            try:
                cls._data = json.loads(cls._path.read_text(encoding="utf-8"))
            except Exception:
                cls._data = {"users": [], "invoices": []}
        else:
            cls._data = {"users": [], "invoices": []}

    @classmethod
    def _save(cls) -> None:
        cls._ensure_loaded()
        cls._path.parent.mkdir(parents=True, exist_ok=True)
        cls._path.write_text(json.dumps(cls._data, default=str, indent=2), encoding="utf-8")

    @classmethod
    def users(cls) -> List[Dict[str, Any]]:
        cls._ensure_loaded()
        return cls._data["users"]  # type: ignore[index]

    @classmethod
    def invoices(cls) -> List[Dict[str, Any]]:
        cls._ensure_loaded()
        return cls._data["invoices"]  # type: ignore[index]

    @classmethod
    def save(cls) -> None:
        cls._save()


def _serialize_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert datetime objects to ISO strings for JSON storage."""
    out: Dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            out[key] = value.isoformat()
        elif isinstance(value, dict):
            out[key] = _serialize_values(value)
        elif isinstance(value, list):
            out[key] = [
                _serialize_values(v) if isinstance(v, dict) else v for v in value
            ]
        else:
            out[key] = value
    return out


class LocalUserRepository:
    """User repository backed by local JSON file."""

    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        users = _LocalStore.users()
        user = _serialize_values(user_data)
        user["_id"] = user.get("_id") or uuid.uuid4().hex
        users.append(user)
        _LocalStore.save()
        return user

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for user in _LocalStore.users():
            if user.get("email") == email:
                return user
        return None

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        for user in _LocalStore.users():
            if str(user.get("_id")) == str(user_id):
                return user
        return None

    async def update(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        users = _LocalStore.users()
        for idx, user in enumerate(users):
            if str(user.get("_id")) == str(user_id):
                updated = {**user, **_serialize_values(update_data), "updated_at": datetime.utcnow().isoformat()}
                users[idx] = updated
                _LocalStore.save()
                return updated
        raise ValueError(f"User not found: {user_id}")

    async def delete(self, user_id: str) -> bool:
        users = _LocalStore.users()
        for idx, user in enumerate(users):
            if str(user.get("_id")) == str(user_id):
                users.pop(idx)
                _LocalStore.save()
                return True
        raise ValueError(f"User not found: {user_id}")

    async def update_last_login(self, user_id: str) -> Dict[str, Any]:
        return await self.update(user_id, {"last_login": datetime.utcnow().isoformat()})


class LocalInvoiceRepository:
    """Invoice repository backed by local JSON file."""

    async def create(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        invoices = _LocalStore.invoices()
        invoice = _serialize_values(invoice_data)
        invoice["_id"] = invoice.get("_id") or uuid.uuid4().hex
        invoices.append(invoice)
        _LocalStore.save()
        return invoice

    async def get_by_id(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        for inv in _LocalStore.invoices():
            if inv.get("invoice_id") == invoice_id:
                return inv
        return None

    async def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        invoices = [inv for inv in _LocalStore.invoices() if str(inv.get("user_id")) == str(user_id)]
        if status:
            invoices = [inv for inv in invoices if inv.get("processing_status") == status]
        invoices.sort(key=lambda x: x.get("upload_time") or "", reverse=True)
        return invoices[skip : skip + limit]

    async def update(self, invoice_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        invoices = _LocalStore.invoices()
        for idx, inv in enumerate(invoices):
            if inv.get("invoice_id") == invoice_id:
                updated = {**inv, **_serialize_values(update_data), "updated_at": datetime.utcnow().isoformat()}
                invoices[idx] = updated
                _LocalStore.save()
                return updated
        raise ValueError(f"Invoice not found: {invoice_id}")

    async def delete(self, invoice_id: str) -> bool:
        invoices = _LocalStore.invoices()
        for idx, inv in enumerate(invoices):
            if inv.get("invoice_id") == invoice_id:
                invoices.pop(idx)
                _LocalStore.save()
                return True
        raise ValueError(f"Invoice not found: {invoice_id}")

    async def count_by_user(self, user_id: str) -> int:
        return len([inv for inv in _LocalStore.invoices() if str(inv.get("user_id")) == str(user_id)])

    async def get_statistics(self, user_id: str) -> Dict[str, Any]:
        stats: Dict[str, int] = {}
        for inv in _LocalStore.invoices():
            if str(inv.get("user_id")) != str(user_id):
                continue
            status = inv.get("processing_status") or "unknown"
            stats[status] = stats.get(status, 0) + 1
        return stats
