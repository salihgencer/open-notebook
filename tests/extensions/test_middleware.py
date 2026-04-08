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
        protected_prefix="/api/ext/",
        excluded_paths=["/api/ext/auth/login", "/api/ext/auth/register"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/api/notebooks")
    async def core_notebooks():
        return {"notebooks": []}

    @app.get("/api/ext/outputs/types")
    async def ext_outputs(request: Request):
        return {"user": request.state.user["sub"]}

    @app.get("/api/ext/auth/login")
    async def ext_login():
        return {"ok": True}

    return app, auth_svc


def test_middleware_passes_through_non_ext_routes(app_with_jwt):
    """Core /api/* routes are NOT protected by JWT middleware."""
    app, _ = app_with_jwt
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200

    resp = client.get("/api/notebooks")
    assert resp.status_code == 200
    assert resp.json() == {"notebooks": []}


def test_middleware_blocks_ext_without_token(app_with_jwt):
    """Extension /api/ext/* routes require JWT token."""
    app, _ = app_with_jwt
    client = TestClient(app)
    resp = client.get("/api/ext/outputs/types")
    assert resp.status_code == 401


def test_middleware_allows_ext_with_valid_token(app_with_jwt):
    app, auth_svc = app_with_jwt
    token = auth_svc.create_access_token(
        user_id="ext_user:123",
        email="test@example.com",
        role="editor",
        locale="en",
    )
    client = TestClient(app)
    resp = client.get("/api/ext/outputs/types", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["user"] == "ext_user:123"


def test_middleware_allows_excluded_ext_paths(app_with_jwt):
    """Login/register don't need JWT."""
    app, _ = app_with_jwt
    client = TestClient(app)
    resp = client.get("/api/ext/auth/login")
    assert resp.status_code == 200


def test_middleware_rejects_refresh_token(app_with_jwt):
    app, auth_svc = app_with_jwt
    token = auth_svc.create_refresh_token(user_id="ext_user:123")
    client = TestClient(app)
    resp = client.get("/api/ext/outputs/types", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
