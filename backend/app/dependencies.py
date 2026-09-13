from typing import Optional
from fastapi import Depends, Header
from backend.app.config import settings
from backend.core.exceptions import UnauthorizedException
from backend.core.security import decode_access_token
from backend.database.repositories.user_repo import user_repo
from backend.models.user import UserOut


async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> UserOut:
    default_user = UserOut(
        id="demo_user_id",
        username="demo_user",
        email="demo@example.com",
        full_name="Demo User",
    )

    if settings.AUTH_DISABLED:
        return default_user

    if not authorization or not authorization.startswith("Bearer "):
        return default_user

    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Invalid authentication token")

    username = payload["sub"]
    user_dict = await user_repo.get_by_username(username)
    if not user_dict:
        return default_user

    return UserOut(**user_dict)
