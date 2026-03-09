from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from backend.core.logging import logger
from backend.database.mysql import MySQLClient


class UserRepository:
    """User CRUD operations with MySQL."""

    @staticmethod
    def _row_to_user(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        user = dict(row)
        user["_id"] = str(user.pop("id"))
        user["is_active"] = bool(user.get("is_active", 1))
        user["is_verified"] = bool(user.get("is_verified", 0))
        user["notifications_enabled"] = bool(user.get("notifications_enabled", 1))
        return user

    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        user_id = str(user_data.get("_id") or uuid.uuid4().hex)
        now = datetime.utcnow()
        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO users (
                        id, email, password_hash, full_name, company, role,
                        is_active, is_verified, created_at, updated_at,
                        last_login, notifications_enabled, theme
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        user_data["email"],
                        user_data["password_hash"],
                        user_data["full_name"],
                        user_data.get("company"),
                        user_data.get("role", "user"),
                        int(bool(user_data.get("is_active", True))),
                        int(bool(user_data.get("is_verified", False))),
                        user_data.get("created_at") or now,
                        user_data.get("updated_at") or now,
                        user_data.get("last_login"),
                        int(bool(user_data.get("notifications_enabled", True))),
                        user_data.get("theme", "light"),
                    ),
                )
        logger.info("User created: %s", user_id)
        created = await self.get_by_id(user_id)
        if not created:
            raise RuntimeError("Failed to fetch created user")
        return created

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE email = %s LIMIT 1", (email,))
                row = await cur.fetchone()
        return self._row_to_user(row)

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT * FROM users WHERE id = %s LIMIT 1", (user_id,))
                row = await cur.fetchone()
        return self._row_to_user(row)

    async def update(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        field_map = {
            "email": "email",
            "password_hash": "password_hash",
            "full_name": "full_name",
            "company": "company",
            "role": "role",
            "is_active": "is_active",
            "is_verified": "is_verified",
            "last_login": "last_login",
            "notifications_enabled": "notifications_enabled",
            "theme": "theme",
        }
        assignments = []
        values = []

        for key, value in update_data.items():
            column = field_map.get(key)
            if not column:
                continue
            if key in {"is_active", "is_verified", "notifications_enabled"} and value is not None:
                value = int(bool(value))
            assignments.append(f"{column} = %s")
            values.append(value)

        if not assignments:
            existing = await self.get_by_id(user_id)
            if not existing:
                raise ValueError(f"User not found: {user_id}")
            return existing

        assignments.append("updated_at = %s")
        values.append(datetime.utcnow())
        values.append(user_id)

        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    f"UPDATE users SET {', '.join(assignments)} WHERE id = %s",
                    tuple(values),
                )
                if cur.rowcount == 0:
                    raise ValueError(f"User not found: {user_id}")

        logger.info("User updated: %s", user_id)
        updated = await self.get_by_id(user_id)
        if not updated:
            raise ValueError(f"User not found: {user_id}")
        return updated

    async def delete(self, user_id: str) -> bool:
        pool = MySQLClient.get_pool()
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
                if cur.rowcount == 0:
                    raise ValueError(f"User not found: {user_id}")
        logger.info("User deleted: %s", user_id)
        return True

    async def update_last_login(self, user_id: str) -> Dict[str, Any]:
        return await self.update(user_id, {"last_login": datetime.utcnow()})
