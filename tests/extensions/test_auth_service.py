import pytest
from extensions.auth.service import AuthService


@pytest.fixture
def auth_service():
    return AuthService(jwt_secret="test-secret-key-that-is-long-enough-for-hs256")


def test_password_hashing(auth_service):
    password = "mySecurePassword123"
    hashed = auth_service.hash_password(password)
    assert hashed != password
    assert auth_service.verify_password(password, hashed) is True
    assert auth_service.verify_password("wrongpassword", hashed) is False


def test_create_access_token(auth_service):
    token = auth_service.create_access_token(
        user_id="ext_user:abc123",
        email="test@example.com",
        role="editor",
        locale="en",
    )
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token(auth_service):
    token = auth_service.create_access_token(
        user_id="ext_user:abc123",
        email="test@example.com",
        role="editor",
        locale="tr",
    )
    payload = auth_service.decode_token(token)
    assert payload["sub"] == "ext_user:abc123"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "editor"
    assert payload["locale"] == "tr"


def test_decode_invalid_token_raises(auth_service):
    with pytest.raises(ValueError, match="Invalid token"):
        auth_service.decode_token("invalid.jwt.token")


def test_create_refresh_token(auth_service):
    token = auth_service.create_refresh_token(user_id="ext_user:abc123")
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_refresh_token(auth_service):
    token = auth_service.create_refresh_token(user_id="ext_user:abc123")
    payload = auth_service.decode_token(token)
    assert payload["sub"] == "ext_user:abc123"
    assert payload["type"] == "refresh"
