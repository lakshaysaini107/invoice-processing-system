from backend.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hashing():
    raw_pw = "SecretPass123!"
    hashed = hash_password(raw_pw)
    assert hashed != raw_pw
    assert verify_password(raw_pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation():
    data = {"sub": "testuser", "role": "admin"}
    token = create_access_token(data)
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded.get("sub") == "testuser"
    assert decoded.get("role") == "admin"
