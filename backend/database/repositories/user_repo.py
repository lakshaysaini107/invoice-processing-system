import uuid
from typing import Dict, Optional
from backend.database.mysql import db_manager
from backend.models.user import UserCreate, UserOut


class UserRepository:
    async def create(self, user: UserCreate, hashed_pw: str) -> UserOut:
        user_id = str(uuid.uuid4())
        query = """
        INSERT INTO users (id, username, email, hashed_password, full_name)
        VALUES (%s, %s, %s, %s, %s)
        """
        await db_manager.execute_query(
            query, (user_id, user.username, user.email, hashed_pw, user.full_name)
        )
        return UserOut(
            id=user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
        )

    async def get_by_username(self, username: str) -> Optional[Dict]:
        query = "SELECT * FROM users WHERE username = %s"
        rows = await db_manager.execute_query(query, (username,))
        return rows[0] if rows else None

    async def get_by_id(self, user_id: str) -> Optional[Dict]:
        query = "SELECT * FROM users WHERE id = %s"
        rows = await db_manager.execute_query(query, (user_id,))
        return rows[0] if rows else None


user_repo = UserRepository()
