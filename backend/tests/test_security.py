import bcrypt

from backend.core.security import PBKDF2_SCHEME, hash_password, verify_password


def test_hash_password_uses_pbkdf2_scheme():
    password = "StrongPass123!"
    hashed = hash_password(password)

    assert hashed.startswith(f"{PBKDF2_SCHEME}$")
    assert verify_password(password, hashed)


def test_verify_password_rejects_invalid_plaintext():
    hashed = hash_password("StrongPass123!")
    assert not verify_password("WrongPass123!", hashed)


def test_verify_password_supports_legacy_bcrypt_hashes():
    legacy_hash = bcrypt.hashpw(b"LegacyPass123!", bcrypt.gensalt()).decode("utf-8")

    assert verify_password("LegacyPass123!", legacy_hash)
    assert not verify_password("WrongPass123!", legacy_hash)


def test_hash_password_supports_long_passwords():
    long_password = "x" * 200
    hashed = hash_password(long_password)

    assert verify_password(long_password, hashed)
