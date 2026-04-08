import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI, Request

from extensions.auth.middleware import JWTAuthMiddleware
from extensions.auth.service import AuthService


@pytest.fixture
def app_with_jwt():
    app = FastAPI()
    auth_svc = AuthService(jwt_secret="test-secret-key-that-is-long-enough-for-hs256")

    app.add_middleware(
        JWTAuthMiddleware,
        auth_service=auth_svc,
        excluded_paths=["/health", "/api/ext/auth/login", "/api/ext/auth/register"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/protected")
    async def protected(request: Request):
        return {"user": request.state.user["sub"]}

    return app, auth_svc


def test_middleware_allows_excluded_paths(app_with_jwt):
    app, _ = app_with_jwt
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200


def test_middleware_blocks_without_token(app_with_jwt):
    app, _ = app_with_jwt
    client = TestClient(app)
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_middleware_allows_with_valid_token(app_with_jwt):
    app, auth_svc = app_with_jwt
    token = auth_svc.create_access_token(
        user_id="ext_user:123",
        email="test@example.com",
        role="editor",
        locale="en",
    )
    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["user"] == "ext_user:123"


def test_middleware_rejects_refresh_token(app_with_jwt):
    app, auth_svc = app_with_jwt
    token = auth_svc.create_refresh_token(user_id="ext_user:123")
    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
