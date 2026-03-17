from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import base64
import binascii
import hashlib
import hmac
import os

import bcrypt
from jose import JWTError, jwt

from backend.app.config import settings
from backend.core.logging import logger


PBKDF2_SCHEME = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 390000
PBKDF2_SALT_BYTES = 16


def _b64_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64_decode(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def _hash_pbkdf2(password: str) -> str:
    salt = os.urandom(PBKDF2_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return (
        f"{PBKDF2_SCHEME}$"
        f"{PBKDF2_ITERATIONS}$"
        f"{_b64_encode(salt)}$"
        f"{_b64_encode(digest)}"
    )


def _verify_pbkdf2(password: str, hashed_password: str) -> bool:
    parts = hashed_password.split("$")
    if len(parts) != 4 or parts[0] != PBKDF2_SCHEME:
        return False

    try:
        iterations = int(parts[1])
        salt = _b64_decode(parts[2])
        expected_digest = _b64_decode(parts[3])
    except (ValueError, binascii.Error):
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(candidate_digest, expected_digest)


def _verify_legacy_bcrypt(password: str, hashed_password: str) -> bool:
    password_bytes = password.encode("utf-8")
    hash_bytes = hashed_password.encode("utf-8")
    try:
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except ValueError as exc:
        # bcrypt only evaluates the first 72 bytes of the password.
        if "72 bytes" in str(exc):
            return bcrypt.checkpw(password_bytes[:72], hash_bytes)
        logger.warning("Legacy bcrypt verification failed: %s", exc)
        return False
    except Exception as exc:
        logger.warning("Legacy bcrypt verification failed: %s", exc)
        return False


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256."""
    return _hash_pbkdf2(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against PBKDF2 hashes and legacy bcrypt hashes."""
    if not hashed_password:
        return False

    if hashed_password.startswith(f"{PBKDF2_SCHEME}$"):
        return _verify_pbkdf2(plain_password, hashed_password)

    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        return _verify_legacy_bcrypt(plain_password, hashed_password)

    return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.error(f"Token verification failed: {str(e)}")
        return None


def create_refresh_token(user_id: str) -> str:
    """Create refresh token for re-authentication"""
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(
        {"sub": user_id, "type": "refresh"},
        expires_delta
    )


# Re-export get_current_user from dependencies for convenience
from backend.app.dependencies import get_current_user
