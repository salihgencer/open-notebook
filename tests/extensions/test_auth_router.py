import pytest
from unittest.mock import AsyncMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient

from extensions.auth.router import create_auth_router
from extensions.auth.service import AuthService


@pytest.fixture
def auth_svc():
    return AuthService(jwt_secret="test-secret-key-that-is-long-enough-for-hs256")


@pytest.fixture
def app(auth_svc):
    app = FastAPI()
    router = create_auth_router(auth_svc)
    app.include_router(router, prefix="/api/ext/auth")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@patch("extensions.auth.router.repo_query", new_callable=AsyncMock)
@patch("extensions.auth.router.repo_create", new_callable=AsyncMock)
def test_register_creates_user(mock_create, mock_query, client):
    mock_query.return_value = []
    mock_create.return_value = [
        {
            "id": "ext_user:abc",
            "email": "new@example.com",
            "name": "New User",
            "role": "editor",
            "locale": "en",
            "is_active": True,
            "created": "2026-01-01T00:00:00",
            "updated": "2026-01-01T00:00:00",
        }
    ]
    resp = client.post(
        "/api/ext/auth/register",
        json={
            "email": "new@example.com",
            "name": "New User",
            "password": "securePass123!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert "access_token" in data
    assert "refresh_token" in data


@patch("extensions.auth.router.repo_query", new_callable=AsyncMock)
def test_register_rejects_duplicate_email(mock_query, client):
    mock_query.return_value = [{"id": "ext_user:existing"}]
    resp = client.post(
        "/api/ext/auth/register",
        json={
            "email": "existing@example.com",
            "name": "Dup User",
            "password": "securePass123!",
        },
    )
    assert resp.status_code == 409


@patch("extensions.auth.router.repo_query", new_callable=AsyncMock)
def test_login_with_valid_credentials(mock_query, client, auth_svc):
    hashed = auth_svc.hash_password("myPassword123")
    mock_query.return_value = [
        {
            "id": "ext_user:abc",
            "email": "user@example.com",
            "name": "Test User",
            "password_hash": hashed,
            "role": "editor",
            "locale": "tr",
            "is_active": True,
            "created": "2026-01-01T00:00:00",
            "updated": "2026-01-01T00:00:00",
        }
    ]
    resp = client.post(
        "/api/ext/auth/login",
        json={"email": "user@example.com", "password": "myPassword123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@patch("extensions.auth.router.repo_query", new_callable=AsyncMock)
def test_login_rejects_wrong_password(mock_query, client, auth_svc):
    hashed = auth_svc.hash_password("correctPassword")
    mock_query.return_value = [
        {
            "id": "ext_user:abc",
            "email": "user@example.com",
            "name": "Test User",
            "password_hash": hashed,
            "role": "editor",
            "locale": "en",
            "is_active": True,
            "created": "2026-01-01T00:00:00",
            "updated": "2026-01-01T00:00:00",
        }
    ]
    resp = client.post(
        "/api/ext/auth/login",
        json={"email": "user@example.com", "password": "wrongPassword"},
    )
    assert resp.status_code == 401
