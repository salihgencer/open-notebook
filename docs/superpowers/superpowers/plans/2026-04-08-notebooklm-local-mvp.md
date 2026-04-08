# NotebookLM Local MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fork open-notebook and add JWT auth (RBAC), written output engine (study guide, FAQ, timeline, briefing), i18n support, and remote LLM connectivity.

**Architecture:** Extension-based approach on top of lfnovo/open-notebook. All customizations live in `extensions/` directories (backend) and `frontend/src/extensions/` (frontend). Core open-notebook files are not modified to maintain upstream sync capability. Auth is JWT-based with SurrealDB user tables. Output engine reuses existing RAG/context pipeline and adds structured prompt templates.

**Tech Stack:** Python 3.12+, FastAPI, SurrealDB, Next.js 14+, React, next-intl, PyJWT, bcrypt, pytest, Vitest

---

## File Map

### Backend Extensions

| File | Responsibility |
|---|---|
| `extensions/__init__.py` | Extension package init |
| `extensions/auth/__init__.py` | Auth package init |
| `extensions/auth/models.py` | User, Session Pydantic models (ObjectModel subclass) |
| `extensions/auth/service.py` | Registration, login, token refresh, password hashing |
| `extensions/auth/middleware.py` | JWT verification middleware (replaces PasswordAuthMiddleware) |
| `extensions/auth/router.py` | `/api/ext/auth/*` endpoints |
| `extensions/auth/rbac.py` | Role-based permission checks (dependency functions) |
| `extensions/outputs/__init__.py` | Outputs package init |
| `extensions/outputs/base.py` | BaseOutputGenerator class |
| `extensions/outputs/registry.py` | Auto-discovery and registry of output types |
| `extensions/outputs/study_guide.py` | Study guide generator |
| `extensions/outputs/faq.py` | FAQ generator |
| `extensions/outputs/timeline.py` | Timeline generator |
| `extensions/outputs/briefing.py` | Briefing doc generator |
| `extensions/outputs/router.py` | `/api/ext/outputs/*` endpoints |
| `extensions/i18n/__init__.py` | i18n package init |
| `extensions/i18n/locales/en.json` | English backend messages |
| `extensions/i18n/locales/tr.json` | Turkish backend messages |
| `extensions/i18n/service.py` | Translation lookup service |
| `extensions/i18n/middleware.py` | Accept-Language / user locale middleware |
| `prompts/outputs/study_guide.yaml` | Study guide prompt template |
| `prompts/outputs/faq.yaml` | FAQ prompt template |
| `prompts/outputs/timeline.yaml` | Timeline prompt template |
| `prompts/outputs/briefing.yaml` | Briefing doc prompt template |

### Frontend Extensions

| File | Responsibility |
|---|---|
| `frontend/src/extensions/i18n/locales/en.json` | English UI strings |
| `frontend/src/extensions/i18n/locales/tr.json` | Turkish UI strings |
| `frontend/src/extensions/i18n/config.ts` | i18n configuration |
| `frontend/src/extensions/i18n/provider.tsx` | IntlProvider wrapper |
| `frontend/src/extensions/auth/login-form.tsx` | Login page component |
| `frontend/src/extensions/auth/register-form.tsx` | Registration component |
| `frontend/src/extensions/auth/auth-provider.tsx` | Auth context provider |
| `frontend/src/extensions/auth/use-auth.ts` | Auth hook (token management) |
| `frontend/src/extensions/outputs/output-panel.tsx` | Output generation panel |
| `frontend/src/extensions/outputs/output-viewer.tsx` | Rendered output display |
| `frontend/src/extensions/outputs/output-selector.tsx` | Output type selector dropdown |

### Tests

| File | Responsibility |
|---|---|
| `tests/extensions/__init__.py` | Test package init |
| `tests/extensions/test_auth_models.py` | User model unit tests |
| `tests/extensions/test_auth_service.py` | Auth service unit tests |
| `tests/extensions/test_auth_router.py` | Auth API endpoint tests |
| `tests/extensions/test_rbac.py` | RBAC permission tests |
| `tests/extensions/test_output_base.py` | BaseOutputGenerator tests |
| `tests/extensions/test_output_generators.py` | Individual generator tests |
| `tests/extensions/test_output_router.py` | Output API endpoint tests |
| `tests/extensions/test_i18n.py` | i18n service tests |
| `frontend/src/test/extensions/auth.test.tsx` | Auth component tests |
| `frontend/src/test/extensions/outputs.test.tsx` | Output component tests |

### Config & Integration

| File | Responsibility |
|---|---|
| `config.custom.yaml` | Extension configuration (enabled extensions, defaults) |
| `docker-compose.override.yml` | Extends docker-compose.yml with custom env vars |
| `.env.custom.example` | Example env for extensions (JWT_SECRET, etc.) |

---

## Task 1: Fork & Local Setup

**Files:**
- Create: `docker-compose.override.yml`
- Create: `.env.custom.example`
- Create: `config.custom.yaml`
- Create: `extensions/__init__.py`

- [ ] **Step 1: Fork and clone the repository**

```bash
gh repo fork lfnovo/open-notebook --clone --remote
cd open-notebook
git remote rename origin upstream
git remote add origin <your-repo-url>
git checkout -b develop
```

- [ ] **Step 2: Verify Docker Compose runs**

```bash
docker compose up -d
```

Run: `curl http://localhost:5055/health`
Expected: `{"status":"healthy"}`

Run: `curl http://localhost:8502`
Expected: HTTP 200 (Next.js frontend)

- [ ] **Step 3: Create extension config files**

Create `docker-compose.override.yml`:

```yaml
services:
  open_notebook:
    environment:
      # JWT Auth
      - JWT_SECRET=change-me-to-a-random-64-char-string
      - JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
      - JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

      # Remote LLM (Gemma 4 on H100)
      - REMOTE_LLM_BASE_URL=http://your-h100-server:8000/v1
      - REMOTE_LLM_MODEL_NAME=gemma-4
      - REMOTE_LLM_API_KEY=optional-key

      # i18n
      - DEFAULT_LOCALE=en

      # Extensions
      - EXTENSIONS_ENABLED=auth,outputs,i18n
    volumes:
      - ./extensions:/app/extensions
      - ./config.custom.yaml:/app/config.custom.yaml
      - ./prompts/outputs:/app/prompts/outputs
```

Create `.env.custom.example`:

```env
# JWT Authentication
JWT_SECRET=change-me-to-a-random-64-char-string
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Remote LLM (OpenAI-compatible endpoint)
REMOTE_LLM_BASE_URL=http://your-h100-server:8000/v1
REMOTE_LLM_MODEL_NAME=gemma-4
REMOTE_LLM_API_KEY=

# i18n
DEFAULT_LOCALE=en

# Extensions
EXTENSIONS_ENABLED=auth,outputs,i18n
```

Create `config.custom.yaml`:

```yaml
extensions:
  auth:
    enabled: true
    default_role: editor
    allow_registration: true
  outputs:
    enabled: true
    default_format: markdown
  i18n:
    enabled: true
    default_locale: en
    supported_locales:
      - en
      - tr
```

Create `extensions/__init__.py`:

```python
"""
NotebookLM Local Extensions.
All customizations live here to maintain upstream sync compatibility.
"""
```

- [ ] **Step 4: Commit**

```bash
git add docker-compose.override.yml .env.custom.example config.custom.yaml extensions/__init__.py
git commit -m "chore: add extension infrastructure and config files"
```

---

## Task 2: Auth — User Model & Database

**Files:**
- Create: `extensions/auth/__init__.py`
- Create: `extensions/auth/models.py`
- Create: `tests/extensions/__init__.py`
- Create: `tests/extensions/test_auth_models.py`

- [ ] **Step 1: Write failing test for User model**

Create `tests/extensions/__init__.py`:

```python
"""Tests for NotebookLM Local extensions."""
```

Create `tests/extensions/test_auth_models.py`:

```python
import pytest
from extensions.auth.models import User


def test_user_creation_with_valid_data():
    user = User(
        email="test@example.com",
        name="Test User",
        role="editor",
        locale="en",
    )
    assert user.email == "test@example.com"
    assert user.name == "Test User"
    assert user.role == "editor"
    assert user.locale == "en"
    assert user.password_hash is None


def test_user_role_validation_rejects_invalid():
    with pytest.raises(ValueError, match="Invalid role"):
        User(
            email="test@example.com",
            name="Test User",
            role="superadmin",
            locale="en",
        )


def test_user_email_validation_rejects_invalid():
    with pytest.raises(ValueError, match="Invalid email"):
        User(
            email="not-an-email",
            name="Test User",
            role="editor",
            locale="en",
        )


def test_user_role_defaults_to_editor():
    user = User(email="test@example.com", name="Test User")
    assert user.role == "editor"


def test_user_locale_defaults_to_en():
    user = User(email="test@example.com", name="Test User")
    assert user.locale == "en"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/extensions/test_auth_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'extensions.auth'`

- [ ] **Step 3: Implement User model**

Create `extensions/auth/__init__.py`:

```python
"""Authentication and authorization extension."""
```

Create `extensions/auth/models.py`:

```python
import re
from typing import ClassVar, List, Literal, Optional

from pydantic import Field, field_validator

from open_notebook.domain.base import ObjectModel

VALID_ROLES = ("admin", "editor", "viewer")
Role = Literal["admin", "editor", "viewer"]


class User(ObjectModel):
    table_name: ClassVar[str] = "ext_user"
    email: str
    name: str
    password_hash: Optional[str] = None
    role: Role = "editor"
    locale: str = "en"
    is_active: bool = True

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid email format")
        return v.lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"Invalid role: {v}. Must be one of {VALID_ROLES}")
        return v


class Session(ObjectModel):
    table_name: ClassVar[str] = "ext_session"
    user_id: str
    refresh_token: str
    expires_at: str
    is_revoked: bool = False


class NotebookShare(ObjectModel):
    table_name: ClassVar[str] = "ext_notebook_share"
    notebook_id: str
    user_id: str
    permission: Literal["editor", "viewer"] = "viewer"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/extensions/test_auth_models.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/auth/ tests/extensions/
git commit -m "feat(auth): add User, Session, NotebookShare models"
```

---

## Task 3: Auth — Service Layer (Registration, Login, JWT)

**Files:**
- Create: `extensions/auth/service.py`
- Create: `tests/extensions/test_auth_service.py`

- [ ] **Step 1: Write failing tests for auth service**

Create `tests/extensions/test_auth_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/extensions/test_auth_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'extensions.auth.service'`

- [ ] **Step 3: Implement auth service**

Create `extensions/auth/service.py`:

```python
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from loguru import logger


class AuthService:
    def __init__(
        self,
        jwt_secret: Optional[str] = None,
        access_token_expire_minutes: int = 15,
        refresh_token_expire_days: int = 7,
    ):
        self.jwt_secret = jwt_secret or os.getenv("JWT_SECRET", "")
        if not self.jwt_secret:
            raise ValueError("JWT_SECRET must be set")
        self.access_token_expire_minutes = int(
            os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(access_token_expire_minutes))
        )
        self.refresh_token_expire_days = int(
            os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", str(refresh_token_expire_days))
        )

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str, hashed: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: str,
        locale: str,
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "email": email,
            "role": role,
            "locale": locale,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self.access_token_expire_minutes),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def create_refresh_token(self, user_id: str) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=self.refresh_token_expire_days),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def decode_token(self, token: str) -> Dict[str, Any]:
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/extensions/test_auth_service.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/auth/service.py tests/extensions/test_auth_service.py
git commit -m "feat(auth): add AuthService with JWT and password hashing"
```

---

## Task 4: Auth — RBAC Dependency Functions

**Files:**
- Create: `extensions/auth/rbac.py`
- Create: `tests/extensions/test_rbac.py`

- [ ] **Step 1: Write failing tests for RBAC**

Create `tests/extensions/test_rbac.py`:

```python
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

from extensions.auth.rbac import require_role, get_current_user_from_state


def _make_request(user_data: dict) -> MagicMock:
    request = MagicMock()
    request.state.user = user_data
    return request


def test_get_current_user_returns_user():
    request = _make_request({"sub": "ext_user:1", "role": "editor", "locale": "en"})
    user = get_current_user_from_state(request)
    assert user["sub"] == "ext_user:1"
    assert user["role"] == "editor"


def test_get_current_user_raises_when_no_user():
    request = MagicMock()
    request.state = MagicMock(spec=[])  # no 'user' attribute
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_from_state(request)
    assert exc_info.value.status_code == 401


def test_require_role_admin_allows_admin():
    checker = require_role("admin")
    request = _make_request({"sub": "ext_user:1", "role": "admin"})
    result = checker(request)
    assert result["role"] == "admin"


def test_require_role_admin_blocks_editor():
    checker = require_role("admin")
    request = _make_request({"sub": "ext_user:1", "role": "editor"})
    with pytest.raises(HTTPException) as exc_info:
        checker(request)
    assert exc_info.value.status_code == 403


def test_require_role_editor_allows_editor_and_admin():
    checker = require_role("editor")
    editor_req = _make_request({"sub": "ext_user:1", "role": "editor"})
    admin_req = _make_request({"sub": "ext_user:2", "role": "admin"})
    assert checker(editor_req)["role"] == "editor"
    assert checker(admin_req)["role"] == "admin"


def test_require_role_viewer_allows_all():
    checker = require_role("viewer")
    for role in ("viewer", "editor", "admin"):
        req = _make_request({"sub": "ext_user:1", "role": role})
        assert checker(req)["role"] == role
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/extensions/test_rbac.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'extensions.auth.rbac'`

- [ ] **Step 3: Implement RBAC**

Create `extensions/auth/rbac.py`:

```python
from typing import Any, Callable, Dict

from fastapi import HTTPException, Request

ROLE_HIERARCHY = {
    "admin": 3,
    "editor": 2,
    "viewer": 1,
}


def get_current_user_from_state(request: Request) -> Dict[str, Any]:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_role(minimum_role: str) -> Callable:
    minimum_level = ROLE_HIERARCHY.get(minimum_role, 0)

    def checker(request: Request) -> Dict[str, Any]:
        user = get_current_user_from_state(request)
        user_level = ROLE_HIERARCHY.get(user.get("role", ""), 0)
        if user_level < minimum_level:
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user.get('role')}' insufficient. Requires '{minimum_role}' or higher.",
            )
        return user

    return checker
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/extensions/test_rbac.py -v`
Expected: All 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/auth/rbac.py tests/extensions/test_rbac.py
git commit -m "feat(auth): add RBAC with role hierarchy (admin > editor > viewer)"
```

---

## Task 5: Auth — JWT Middleware

**Files:**
- Create: `extensions/auth/middleware.py`

- [ ] **Step 1: Write failing test for middleware**

Add to `tests/extensions/test_auth_service.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.testclient import TestClient
from fastapi import FastAPI

from extensions.auth.middleware import JWTAuthMiddleware
from extensions.auth.service import AuthService


@pytest.fixture
def app_with_jwt_middleware():
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
    async def protected(request):
        return {"user": request.state.user["sub"]}

    return app, auth_svc


def test_middleware_allows_excluded_paths(app_with_jwt_middleware):
    app, _ = app_with_jwt_middleware
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200


def test_middleware_blocks_without_token(app_with_jwt_middleware):
    app, _ = app_with_jwt_middleware
    client = TestClient(app)
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_middleware_allows_with_valid_token(app_with_jwt_middleware):
    app, auth_svc = app_with_jwt_middleware
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/extensions/test_auth_service.py::test_middleware_allows_excluded_paths -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'extensions.auth.middleware'`

- [ ] **Step 3: Implement JWT middleware**

Create `extensions/auth/middleware.py`:

```python
from typing import List, Optional

from fastapi import Request
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from extensions.auth.service import AuthService


class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        auth_service: AuthService,
        excluded_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.auth_service = auth_service
        self.excluded_paths = excluded_paths or []

    async def dispatch(self, request: Request, call_next):
        # Skip excluded paths
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Skip CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract token
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization header"},
            )

        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() != "bearer":
                raise ValueError("Invalid scheme")
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid authorization header format"},
            )

        # Decode and validate
        try:
            payload = self.auth_service.decode_token(token)
            if payload.get("type") != "access":
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid token type"},
                )
            request.state.user = payload
        except ValueError as e:
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)},
            )

        return await call_next(request)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/extensions/test_auth_service.py -v`
Expected: All 9 tests PASS (6 original + 3 middleware)

- [ ] **Step 5: Commit**

```bash
git add extensions/auth/middleware.py tests/extensions/test_auth_service.py
git commit -m "feat(auth): add JWT middleware with excluded paths support"
```

---

## Task 6: Auth — API Router (Register, Login, Refresh, Me)

**Files:**
- Create: `extensions/auth/router.py`
- Create: `tests/extensions/test_auth_router.py`

- [ ] **Step 1: Write failing tests for auth endpoints**

Create `tests/extensions/test_auth_router.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
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
    mock_query.return_value = []  # no existing user
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
    mock_query.return_value = [{"id": "ext_user:existing"}]  # user exists
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/extensions/test_auth_router.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'extensions.auth.router'`

- [ ] **Step 3: Implement auth router**

Create `extensions/auth/router.py`:

```python
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, EmailStr

from open_notebook.database.repository import repo_create, repo_query
from extensions.auth.service import AuthService


class RegisterRequest(BaseModel):
    email: str
    name: str
    password: str
    locale: Optional[str] = "en"


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    email: str
    name: str
    role: str
    locale: str


def create_auth_router(auth_service: AuthService) -> APIRouter:
    router = APIRouter()

    @router.post("/register", status_code=201)
    async def register(req: RegisterRequest):
        # Check if email already exists
        existing = await repo_query(
            "SELECT id FROM ext_user WHERE email = $email",
            {"email": req.email.lower()},
        )
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")

        # Create user
        password_hash = auth_service.hash_password(req.password)
        result = await repo_create(
            "ext_user",
            {
                "email": req.email.lower(),
                "name": req.name,
                "password_hash": password_hash,
                "role": "editor",
                "locale": req.locale or "en",
                "is_active": True,
            },
        )
        user_data = result[0] if isinstance(result, list) else result
        user_id = user_data["id"]

        access_token = auth_service.create_access_token(
            user_id=user_id,
            email=user_data["email"],
            role=user_data["role"],
            locale=user_data["locale"],
        )
        refresh_token = auth_service.create_refresh_token(user_id=user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            email=user_data["email"],
            name=user_data["name"],
            role=user_data["role"],
            locale=user_data["locale"],
        )

    @router.post("/login")
    async def login(req: LoginRequest):
        users = await repo_query(
            "SELECT * FROM ext_user WHERE email = $email",
            {"email": req.email.lower()},
        )
        if not users:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user = users[0]
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account disabled")

        if not auth_service.verify_password(req.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        access_token = auth_service.create_access_token(
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
            locale=user.get("locale", "en"),
        )
        refresh_token = auth_service.create_refresh_token(user_id=user["id"])

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            email=user["email"],
            name=user["name"],
            role=user["role"],
            locale=user.get("locale", "en"),
        )

    @router.post("/refresh")
    async def refresh(req: RefreshRequest):
        try:
            payload = auth_service.decode_token(req.refresh_token)
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))

        user_id = payload["sub"]
        users = await repo_query(
            "SELECT * FROM $id",
            {"id": user_id},
        )
        if not users:
            raise HTTPException(status_code=401, detail="User not found")

        user = users[0]
        access_token = auth_service.create_access_token(
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
            locale=user.get("locale", "en"),
        )
        new_refresh = auth_service.create_refresh_token(user_id=user["id"])

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh,
            email=user["email"],
            name=user["name"],
            role=user["role"],
            locale=user.get("locale", "en"),
        )

    @router.get("/me")
    async def me(request: Request):
        user = getattr(request.state, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return {
            "id": user["sub"],
            "email": user["email"],
            "role": user["role"],
            "locale": user["locale"],
        }

    return router
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/extensions/test_auth_router.py -v`
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/auth/router.py tests/extensions/test_auth_router.py
git commit -m "feat(auth): add register, login, refresh, me endpoints"
```

---

## Task 7: Output Engine — Base Generator & Registry

**Files:**
- Create: `extensions/outputs/__init__.py`
- Create: `extensions/outputs/base.py`
- Create: `extensions/outputs/registry.py`
- Create: `tests/extensions/test_output_base.py`

- [ ] **Step 1: Write failing tests**

Create `tests/extensions/test_output_base.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch

from extensions.outputs.base import BaseOutputGenerator
from extensions.outputs.registry import OutputRegistry


class MockGenerator(BaseOutputGenerator):
    name = "mock_output"
    title = "Mock Output"
    description = "A mock output for testing"
    sections = ["intro", "body"]
    prompt_template = "Generate a {output_type} about:\n{context}\nLanguage: {language}"

    def format_output(self, raw_text: str) -> str:
        return f"# Mock Output\n\n{raw_text}"


def test_base_generator_has_required_attributes():
    gen = MockGenerator()
    assert gen.name == "mock_output"
    assert gen.title == "Mock Output"
    assert gen.sections == ["intro", "body"]


def test_base_generator_builds_prompt():
    gen = MockGenerator()
    prompt = gen.build_prompt(
        context="Some context about AI",
        language="tr",
    )
    assert "mock_output" in prompt.lower() or "Mock Output" in prompt
    assert "Some context about AI" in prompt
    assert "tr" in prompt


def test_format_output():
    gen = MockGenerator()
    result = gen.format_output("Test content")
    assert result.startswith("# Mock Output")
    assert "Test content" in result


def test_registry_discovers_generators():
    registry = OutputRegistry()
    registry.register(MockGenerator)
    assert "mock_output" in registry.list_types()
    gen = registry.get("mock_output")
    assert isinstance(gen, MockGenerator)


def test_registry_returns_none_for_unknown():
    registry = OutputRegistry()
    assert registry.get("nonexistent") is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/extensions/test_output_base.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement base generator and registry**

Create `extensions/outputs/__init__.py`:

```python
"""Written output generation extension."""
```

Create `extensions/outputs/base.py`:

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseOutputGenerator(ABC):
    name: str = ""
    title: str = ""
    description: str = ""
    sections: List[str] = []
    prompt_template: str = ""

    def build_prompt(self, context: str, language: str = "en") -> str:
        return self.prompt_template.format(
            output_type=self.title,
            context=context,
            language=language,
            sections=", ".join(self.sections),
        )

    def format_output(self, raw_text: str) -> str:
        return raw_text
```

Create `extensions/outputs/registry.py`:

```python
from typing import Dict, List, Optional, Type

from extensions.outputs.base import BaseOutputGenerator


class OutputRegistry:
    def __init__(self):
        self._generators: Dict[str, Type[BaseOutputGenerator]] = {}

    def register(self, generator_class: Type[BaseOutputGenerator]) -> None:
        self._generators[generator_class.name] = generator_class

    def get(self, name: str) -> Optional[BaseOutputGenerator]:
        cls = self._generators.get(name)
        return cls() if cls else None

    def list_types(self) -> List[str]:
        return list(self._generators.keys())

    def list_all(self) -> List[Dict[str, str]]:
        return [
            {
                "name": cls.name,
                "title": cls.title,
                "description": cls.description,
            }
            for cls in self._generators.values()
        ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/extensions/test_output_base.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/outputs/ tests/extensions/test_output_base.py
git commit -m "feat(outputs): add BaseOutputGenerator and OutputRegistry"
```

---

## Task 8: Output Engine — Study Guide, FAQ, Timeline, Briefing Generators

**Files:**
- Create: `extensions/outputs/study_guide.py`
- Create: `extensions/outputs/faq.py`
- Create: `extensions/outputs/timeline.py`
- Create: `extensions/outputs/briefing.py`
- Create: `prompts/outputs/study_guide.yaml`
- Create: `prompts/outputs/faq.yaml`
- Create: `prompts/outputs/timeline.yaml`
- Create: `prompts/outputs/briefing.yaml`
- Create: `tests/extensions/test_output_generators.py`

- [ ] **Step 1: Write failing tests**

Create `tests/extensions/test_output_generators.py`:

```python
import pytest

from extensions.outputs.study_guide import StudyGuideGenerator
from extensions.outputs.faq import FAQGenerator
from extensions.outputs.timeline import TimelineGenerator
from extensions.outputs.briefing import BriefingGenerator
from extensions.outputs.registry import OutputRegistry


@pytest.fixture
def registry():
    reg = OutputRegistry()
    reg.register(StudyGuideGenerator)
    reg.register(FAQGenerator)
    reg.register(TimelineGenerator)
    reg.register(BriefingGenerator)
    return reg


def test_all_generators_registered(registry):
    types = registry.list_types()
    assert "study_guide" in types
    assert "faq" in types
    assert "timeline" in types
    assert "briefing" in types


def test_study_guide_prompt_contains_sections():
    gen = StudyGuideGenerator()
    prompt = gen.build_prompt(context="AI fundamentals", language="en")
    assert "AI fundamentals" in prompt
    assert "en" in prompt


def test_faq_prompt_contains_context():
    gen = FAQGenerator()
    prompt = gen.build_prompt(context="Machine learning basics", language="tr")
    assert "Machine learning basics" in prompt
    assert "tr" in prompt


def test_timeline_prompt_contains_context():
    gen = TimelineGenerator()
    prompt = gen.build_prompt(context="History of computing", language="en")
    assert "History of computing" in prompt


def test_briefing_prompt_contains_context():
    gen = BriefingGenerator()
    prompt = gen.build_prompt(context="Quarterly report data", language="tr")
    assert "Quarterly report data" in prompt


def test_each_generator_has_required_fields():
    for GenClass in [StudyGuideGenerator, FAQGenerator, TimelineGenerator, BriefingGenerator]:
        gen = GenClass()
        assert gen.name, f"{GenClass.__name__} missing name"
        assert gen.title, f"{GenClass.__name__} missing title"
        assert gen.description, f"{GenClass.__name__} missing description"
        assert len(gen.sections) > 0, f"{GenClass.__name__} has no sections"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/extensions/test_output_generators.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement generators**

Create `extensions/outputs/study_guide.py`:

```python
from extensions.outputs.base import BaseOutputGenerator


class StudyGuideGenerator(BaseOutputGenerator):
    name = "study_guide"
    title = "Study Guide"
    description = "Generates a structured study guide with key concepts, definitions, review questions, and summary."
    sections = ["overview", "key_concepts", "review_questions", "summary"]
    prompt_template = """You are a study guide generator. Create a comprehensive study guide from the following source material.

## Source Material
{context}

## Requirements
- Language: {language}
- Output format: Markdown
- Sections to include: {sections}

## Instructions
1. **Overview**: Brief introduction to the topic (2-3 sentences)
2. **Key Concepts**: List and explain each key concept with clear definitions
3. **Review Questions**: Generate 5-10 questions that test understanding of the material
4. **Summary**: Concise summary of the most important takeaways

Write clearly and concisely. Focus on the most important information from the sources."""
```

Create `extensions/outputs/faq.py`:

```python
from extensions.outputs.base import BaseOutputGenerator


class FAQGenerator(BaseOutputGenerator):
    name = "faq"
    title = "FAQ"
    description = "Generates frequently asked questions and answers based on source material."
    sections = ["questions_and_answers"]
    prompt_template = """You are a FAQ generator. Extract the most important questions and provide clear answers from the source material.

## Source Material
{context}

## Requirements
- Language: {language}
- Output format: Markdown
- Generate 8-15 question-answer pairs

## Instructions
1. Identify the key topics and common questions someone would ask about this material
2. Write each question as someone unfamiliar with the topic would ask it
3. Provide clear, concise answers grounded in the source material
4. Order questions from most fundamental to most specific

Format each Q&A as:
### Q: [Question]
**A:** [Answer]"""
```

Create `extensions/outputs/timeline.py`:

```python
from extensions.outputs.base import BaseOutputGenerator


class TimelineGenerator(BaseOutputGenerator):
    name = "timeline"
    title = "Timeline"
    description = "Generates a chronological timeline of events, milestones, and developments."
    sections = ["events", "context"]
    prompt_template = """You are a timeline generator. Extract chronological events and milestones from the source material.

## Source Material
{context}

## Requirements
- Language: {language}
- Output format: Markdown
- Order events chronologically

## Instructions
1. Identify all dates, periods, and chronological references in the material
2. For each event, provide: date/period, event title, and brief context (1-2 sentences)
3. If exact dates aren't available, use relative ordering or approximate periods
4. Highlight key turning points or milestones

Format as:
### [Date/Period]
**[Event Title]**
[Brief context and significance]"""
```

Create `extensions/outputs/briefing.py`:

```python
from extensions.outputs.base import BaseOutputGenerator


class BriefingGenerator(BaseOutputGenerator):
    name = "briefing"
    title = "Briefing Document"
    description = "Generates an executive briefing with summary, key findings, and recommendations."
    sections = ["executive_summary", "key_findings", "recommendations", "next_steps"]
    prompt_template = """You are a briefing document generator. Create a professional executive briefing from the source material.

## Source Material
{context}

## Requirements
- Language: {language}
- Output format: Markdown
- Sections: {sections}
- Tone: Professional, concise, action-oriented

## Instructions
1. **Executive Summary**: 3-5 sentence overview of the most critical information
2. **Key Findings**: Bullet-pointed list of the most important facts and insights
3. **Recommendations**: Actionable recommendations based on the findings
4. **Next Steps**: Concrete next actions to take

Keep the briefing under 500 words. Prioritize actionable information over background details."""
```

- [ ] **Step 4: Create prompt template YAML files**

Create `prompts/outputs/study_guide.yaml`:

```yaml
name: study_guide
title: Study Guide
description: "Generates a structured study guide from notebook sources"
sections:
  - overview
  - key_concepts
  - review_questions
  - summary
output_format: markdown
```

Create `prompts/outputs/faq.yaml`:

```yaml
name: faq
title: FAQ
description: "Generates FAQ from notebook sources"
sections:
  - questions_and_answers
output_format: markdown
```

Create `prompts/outputs/timeline.yaml`:

```yaml
name: timeline
title: Timeline
description: "Generates chronological timeline from notebook sources"
sections:
  - events
  - context
output_format: markdown
```

Create `prompts/outputs/briefing.yaml`:

```yaml
name: briefing
title: Briefing Document
description: "Generates executive briefing from notebook sources"
sections:
  - executive_summary
  - key_findings
  - recommendations
  - next_steps
output_format: markdown
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/extensions/test_output_generators.py -v`
Expected: All 7 tests PASS

- [ ] **Step 6: Commit**

```bash
git add extensions/outputs/ prompts/outputs/ tests/extensions/test_output_generators.py
git commit -m "feat(outputs): add study guide, FAQ, timeline, briefing generators"
```

---

## Task 9: Output Engine — API Router

**Files:**
- Create: `extensions/outputs/router.py`
- Create: `tests/extensions/test_output_router.py`

- [ ] **Step 1: Write failing tests**

Create `tests/extensions/test_output_router.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from extensions.outputs.router import create_outputs_router
from extensions.outputs.registry import OutputRegistry
from extensions.outputs.study_guide import StudyGuideGenerator
from extensions.outputs.faq import FAQGenerator
from extensions.outputs.timeline import TimelineGenerator
from extensions.outputs.briefing import BriefingGenerator


@pytest.fixture
def registry():
    reg = OutputRegistry()
    reg.register(StudyGuideGenerator)
    reg.register(FAQGenerator)
    reg.register(TimelineGenerator)
    reg.register(BriefingGenerator)
    return reg


@pytest.fixture
def app(registry):
    app = FastAPI()
    router = create_outputs_router(registry)
    app.include_router(router, prefix="/api/ext/outputs")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_list_output_types(client):
    resp = client.get("/api/ext/outputs/types")
    assert resp.status_code == 200
    data = resp.json()
    names = [t["name"] for t in data]
    assert "study_guide" in names
    assert "faq" in names
    assert "timeline" in names
    assert "briefing" in names


@patch("extensions.outputs.router.get_notebook_context", new_callable=AsyncMock)
@patch("extensions.outputs.router.call_llm", new_callable=AsyncMock)
def test_generate_output(mock_llm, mock_context, client):
    mock_context.return_value = "Source material about machine learning..."
    mock_llm.return_value = "# Study Guide\n\n## Overview\nML is..."

    resp = client.post(
        "/api/ext/outputs/generate",
        json={
            "notebook_id": "notebook:abc123",
            "output_type": "study_guide",
            "language": "en",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "content" in data
    assert data["output_type"] == "study_guide"


@patch("extensions.outputs.router.get_notebook_context", new_callable=AsyncMock)
@patch("extensions.outputs.router.call_llm", new_callable=AsyncMock)
def test_generate_unknown_type_returns_404(mock_llm, mock_context, client):
    resp = client.post(
        "/api/ext/outputs/generate",
        json={
            "notebook_id": "notebook:abc123",
            "output_type": "nonexistent",
            "language": "en",
        },
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/extensions/test_output_router.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement outputs router**

Create `extensions/outputs/router.py`:

```python
from typing import Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from open_notebook.database.repository import ensure_record_id, repo_query
from extensions.outputs.registry import OutputRegistry


class GenerateRequest(BaseModel):
    notebook_id: str
    output_type: str
    language: str = "en"
    model_id: Optional[str] = None


class GenerateResponse(BaseModel):
    content: str
    output_type: str
    language: str


async def get_notebook_context(notebook_id: str) -> str:
    """Gather all source content from a notebook for output generation."""
    sources = await repo_query(
        """
        SELECT in.full_text as text, in.title as title
        FROM reference WHERE out = $notebook_id
        """,
        {"notebook_id": ensure_record_id(notebook_id)},
    )
    if not sources:
        return ""

    parts = []
    for src in sources:
        title = src.get("title", "Untitled")
        text = src.get("text", "")
        if text:
            parts.append(f"### {title}\n{text}")

    return "\n\n---\n\n".join(parts)


async def call_llm(prompt: str, model_id: Optional[str] = None) -> str:
    """Call LLM using open-notebook's existing Esperanto/LangChain infrastructure."""
    from open_notebook.ai.chat import chat_completion

    response = await chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model_id=model_id,
    )
    return response


def create_outputs_router(registry: OutputRegistry) -> APIRouter:
    router = APIRouter()

    @router.get("/types")
    async def list_types():
        return registry.list_all()

    @router.post("/generate", response_model=GenerateResponse)
    async def generate(req: GenerateRequest):
        generator = registry.get(req.output_type)
        if not generator:
            raise HTTPException(
                status_code=404,
                detail=f"Output type '{req.output_type}' not found. Available: {registry.list_types()}",
            )

        context = await get_notebook_context(req.notebook_id)
        if not context:
            raise HTTPException(
                status_code=400,
                detail="Notebook has no sources with content",
            )

        prompt = generator.build_prompt(context=context, language=req.language)
        raw_output = await call_llm(prompt, model_id=req.model_id)
        formatted = generator.format_output(raw_output)

        return GenerateResponse(
            content=formatted,
            output_type=req.output_type,
            language=req.language,
        )

    return router
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/extensions/test_output_router.py -v`
Expected: All 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/outputs/router.py tests/extensions/test_output_router.py
git commit -m "feat(outputs): add API router for output generation"
```

---

## Task 10: i18n — Backend Service & Middleware

**Files:**
- Create: `extensions/i18n/__init__.py`
- Create: `extensions/i18n/service.py`
- Create: `extensions/i18n/middleware.py`
- Create: `extensions/i18n/locales/en.json`
- Create: `extensions/i18n/locales/tr.json`
- Create: `tests/extensions/test_i18n.py`

- [ ] **Step 1: Write failing tests**

Create `tests/extensions/test_i18n.py`:

```python
import pytest
import os

from extensions.i18n.service import I18nService


@pytest.fixture
def i18n():
    locales_dir = os.path.join(os.path.dirname(__file__), "../../extensions/i18n/locales")
    return I18nService(locales_dir=locales_dir, default_locale="en")


def test_translate_english(i18n):
    result = i18n.t("auth.login_success", locale="en")
    assert isinstance(result, str)
    assert len(result) > 0


def test_translate_turkish(i18n):
    result = i18n.t("auth.login_success", locale="tr")
    assert isinstance(result, str)
    assert result != i18n.t("auth.login_success", locale="en")


def test_fallback_to_default_locale(i18n):
    result = i18n.t("auth.login_success", locale="nonexistent")
    assert result == i18n.t("auth.login_success", locale="en")


def test_missing_key_returns_key(i18n):
    result = i18n.t("nonexistent.key", locale="en")
    assert result == "nonexistent.key"


def test_supported_locales(i18n):
    locales = i18n.supported_locales()
    assert "en" in locales
    assert "tr" in locales
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/extensions/test_i18n.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement i18n service, middleware, and locale files**

Create `extensions/i18n/__init__.py`:

```python
"""Internationalization extension."""
```

Create `extensions/i18n/locales/en.json`:

```json
{
  "auth": {
    "login_success": "Login successful",
    "login_failed": "Invalid email or password",
    "register_success": "Registration successful",
    "email_exists": "Email already registered",
    "token_expired": "Session expired, please login again",
    "unauthorized": "You are not authorized to perform this action",
    "account_disabled": "Account has been disabled"
  },
  "outputs": {
    "generate_success": "Output generated successfully",
    "no_sources": "This notebook has no sources with content",
    "type_not_found": "Output type not found",
    "generating": "Generating output..."
  },
  "common": {
    "save_success": "Saved successfully",
    "delete_success": "Deleted successfully",
    "not_found": "Item not found",
    "server_error": "An unexpected error occurred"
  }
}
```

Create `extensions/i18n/locales/tr.json`:

```json
{
  "auth": {
    "login_success": "Giriş başarılı",
    "login_failed": "Geçersiz e-posta veya şifre",
    "register_success": "Kayıt başarılı",
    "email_exists": "Bu e-posta adresi zaten kayıtlı",
    "token_expired": "Oturum süresi doldu, lütfen tekrar giriş yapın",
    "unauthorized": "Bu işlemi gerçekleştirmek için yetkiniz yok",
    "account_disabled": "Hesap devre dışı bırakılmış"
  },
  "outputs": {
    "generate_success": "Çıktı başarıyla oluşturuldu",
    "no_sources": "Bu not defterinde içerik bulunan kaynak yok",
    "type_not_found": "Çıktı türü bulunamadı",
    "generating": "Çıktı oluşturuluyor..."
  },
  "common": {
    "save_success": "Başarıyla kaydedildi",
    "delete_success": "Başarıyla silindi",
    "not_found": "Öğe bulunamadı",
    "server_error": "Beklenmeyen bir hata oluştu"
  }
}
```

Create `extensions/i18n/service.py`:

```python
import json
import os
from typing import Any, Dict, List, Optional

from loguru import logger


class I18nService:
    def __init__(self, locales_dir: str, default_locale: str = "en"):
        self.default_locale = default_locale
        self._translations: Dict[str, Dict[str, Any]] = {}
        self._load_locales(locales_dir)

    def _load_locales(self, locales_dir: str) -> None:
        if not os.path.isdir(locales_dir):
            logger.warning(f"Locales directory not found: {locales_dir}")
            return

        for filename in os.listdir(locales_dir):
            if filename.endswith(".json"):
                locale = filename[:-5]  # remove .json
                filepath = os.path.join(locales_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        self._translations[locale] = json.load(f)
                    logger.info(f"Loaded locale: {locale}")
                except Exception as e:
                    logger.error(f"Failed to load locale {locale}: {e}")

    def t(self, key: str, locale: Optional[str] = None, **kwargs) -> str:
        loc = locale if locale in self._translations else self.default_locale
        translations = self._translations.get(loc, {})

        # Navigate nested keys (e.g., "auth.login_success")
        parts = key.split(".")
        value = translations
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return key  # key not found

        if value is None:
            return key

        if isinstance(value, str) and kwargs:
            try:
                return value.format(**kwargs)
            except KeyError:
                return value

        return str(value) if value else key

    def supported_locales(self) -> List[str]:
        return list(self._translations.keys())
```

Create `extensions/i18n/middleware.py`:

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from extensions.i18n.service import I18nService


class LocaleMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, i18n_service: I18nService):
        super().__init__(app)
        self.i18n = i18n_service

    async def dispatch(self, request: Request, call_next):
        # Priority: 1. JWT locale, 2. Accept-Language header, 3. default
        locale = self.i18n.default_locale

        # Check JWT user locale (set by auth middleware)
        user = getattr(request.state, "user", None)
        if user and "locale" in user:
            locale = user["locale"]
        else:
            # Fallback to Accept-Language header
            accept_lang = request.headers.get("Accept-Language", "")
            if accept_lang:
                # Parse first language tag (e.g., "tr-TR,tr;q=0.9" -> "tr")
                primary = accept_lang.split(",")[0].split(";")[0].strip()
                lang_code = primary.split("-")[0].lower()
                if lang_code in self.i18n.supported_locales():
                    locale = lang_code

        request.state.locale = locale
        request.state.i18n = self.i18n
        response = await call_next(request)
        return response
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/extensions/test_i18n.py -v`
Expected: All 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add extensions/i18n/ tests/extensions/test_i18n.py
git commit -m "feat(i18n): add I18nService, LocaleMiddleware, and TR/EN locale files"
```

---

## Task 11: Integration — Wire Extensions into main.py

**Files:**
- Create: `extensions/loader.py`

This is the only file that touches the integration point with open-notebook's `api/main.py`. The loader dynamically registers extension routers and middleware so that `main.py` only needs a single import line added.

- [ ] **Step 1: Create extension loader**

Create `extensions/loader.py`:

```python
"""
Extension loader — single integration point with open-notebook core.
Registers all extension routers and middleware on the FastAPI app.
"""

import os
from typing import Optional

from fastapi import FastAPI
from loguru import logger

from extensions.auth.middleware import JWTAuthMiddleware
from extensions.auth.router import create_auth_router
from extensions.auth.service import AuthService
from extensions.i18n.middleware import LocaleMiddleware
from extensions.i18n.service import I18nService
from extensions.outputs.briefing import BriefingGenerator
from extensions.outputs.faq import FAQGenerator
from extensions.outputs.registry import OutputRegistry
from extensions.outputs.router import create_outputs_router
from extensions.outputs.study_guide import StudyGuideGenerator
from extensions.outputs.timeline import TimelineGenerator


def load_extensions(app: FastAPI) -> None:
    """Load all enabled extensions onto the FastAPI app."""
    enabled = os.getenv("EXTENSIONS_ENABLED", "").split(",")
    enabled = [e.strip() for e in enabled if e.strip()]

    if not enabled:
        logger.info("No extensions enabled (EXTENSIONS_ENABLED is empty)")
        return

    logger.info(f"Loading extensions: {enabled}")

    auth_service: Optional[AuthService] = None

    # Auth extension
    if "auth" in enabled:
        jwt_secret = os.getenv("JWT_SECRET")
        if not jwt_secret:
            logger.error("JWT_SECRET not set — auth extension disabled")
        else:
            auth_service = AuthService(jwt_secret=jwt_secret)
            auth_router = create_auth_router(auth_service)
            app.include_router(auth_router, prefix="/api/ext/auth", tags=["ext-auth"])

            # Add JWT middleware (must be added after CORS)
            app.add_middleware(
                JWTAuthMiddleware,
                auth_service=auth_service,
                excluded_paths=[
                    "/",
                    "/health",
                    "/docs",
                    "/openapi.json",
                    "/redoc",
                    "/api/ext/auth/login",
                    "/api/ext/auth/register",
                    "/api/auth/status",
                    "/api/config",
                ],
            )
            logger.success("Auth extension loaded")

    # i18n extension
    if "i18n" in enabled:
        locales_dir = os.path.join(
            os.path.dirname(__file__), "i18n", "locales"
        )
        default_locale = os.getenv("DEFAULT_LOCALE", "en")
        i18n_service = I18nService(locales_dir=locales_dir, default_locale=default_locale)
        app.add_middleware(LocaleMiddleware, i18n_service=i18n_service)
        logger.success(f"i18n extension loaded (default: {default_locale}, locales: {i18n_service.supported_locales()})")

    # Outputs extension
    if "outputs" in enabled:
        registry = OutputRegistry()
        registry.register(StudyGuideGenerator)
        registry.register(FAQGenerator)
        registry.register(TimelineGenerator)
        registry.register(BriefingGenerator)
        outputs_router = create_outputs_router(registry)
        app.include_router(outputs_router, prefix="/api/ext/outputs", tags=["ext-outputs"])
        logger.success(f"Outputs extension loaded ({registry.list_types()})")
```

- [ ] **Step 2: Document the single-line integration**

The only change needed in `api/main.py` is adding these lines after the existing router includes:

```python
# Extensions (add after all app.include_router calls)
try:
    from extensions.loader import load_extensions
    load_extensions(app)
except ImportError:
    pass  # Extensions not installed
```

This is the minimal core touch — a try/except that gracefully does nothing if extensions aren't present, keeping upstream compatibility intact.

- [ ] **Step 3: Commit**

```bash
git add extensions/loader.py
git commit -m "feat: add extension loader — single integration point for all extensions"
```

---

## Task 12: Frontend — Auth Provider & Login

**Files:**
- Create: `frontend/src/extensions/auth/auth-provider.tsx`
- Create: `frontend/src/extensions/auth/use-auth.ts`
- Create: `frontend/src/extensions/auth/login-form.tsx`
- Create: `frontend/src/extensions/auth/register-form.tsx`

- [ ] **Step 1: Create auth hook and provider**

Create `frontend/src/extensions/auth/use-auth.ts`:

```typescript
import { useState, useCallback } from "react";

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  locale: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

const TOKEN_KEY = "notebooklm_access_token";
const REFRESH_KEY = "notebooklm_refresh_token";
const USER_KEY = "notebooklm_user";

export function useAuth() {
  const [state, setState] = useState<AuthState>(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    const user = localStorage.getItem(USER_KEY);
    return {
      accessToken: token,
      refreshToken: localStorage.getItem(REFRESH_KEY),
      user: user ? JSON.parse(user) : null,
      isAuthenticated: !!token,
    };
  });

  const login = useCallback(async (email: string, password: string) => {
    const res = await fetch("/api/ext/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Login failed");
    }

    const data = await res.json();
    const user: User = {
      id: data.email, // Will be updated from /me
      email: data.email,
      name: data.name,
      role: data.role,
      locale: data.locale,
    };

    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(REFRESH_KEY, data.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));

    setState({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user,
      isAuthenticated: true,
    });
  }, []);

  const register = useCallback(
    async (email: string, name: string, password: string) => {
      const res = await fetch("/api/ext/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, password }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Registration failed");
      }

      const data = await res.json();
      const user: User = {
        id: data.email,
        email: data.email,
        name: data.name,
        role: data.role,
        locale: data.locale,
      };

      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(REFRESH_KEY, data.refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));

      setState({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        user,
        isAuthenticated: true,
      });
    },
    []
  );

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    setState({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
    });
  }, []);

  return { ...state, login, register, logout };
}
```

Create `frontend/src/extensions/auth/auth-provider.tsx`:

```tsx
"use client";

import React, { createContext, useContext, ReactNode } from "react";
import { useAuth } from "./use-auth";

type AuthContextType = ReturnType<typeof useAuth>;

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const auth = useAuth();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthContext must be used within AuthProvider");
  return ctx;
}
```

Create `frontend/src/extensions/auth/login-form.tsx`:

```tsx
"use client";

import React, { useState } from "react";
import { useAuthContext } from "./auth-provider";

export function LoginForm({ onSwitchToRegister }: { onSwitchToRegister: () => void }) {
  const { login } = useAuthContext();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 w-full max-w-sm mx-auto">
      <h2 className="text-2xl font-bold text-center">Login</h2>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        className="w-full p-2 border rounded"
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        className="w-full p-2 border rounded"
      />
      <button
        type="submit"
        disabled={loading}
        className="w-full p-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {loading ? "Logging in..." : "Login"}
      </button>
      <p className="text-center text-sm">
        Don't have an account?{" "}
        <button type="button" onClick={onSwitchToRegister} className="text-blue-600 underline">
          Register
        </button>
      </p>
    </form>
  );
}
```

Create `frontend/src/extensions/auth/register-form.tsx`:

```tsx
"use client";

import React, { useState } from "react";
import { useAuthContext } from "./auth-provider";

export function RegisterForm({ onSwitchToLogin }: { onSwitchToLogin: () => void }) {
  const { register } = useAuthContext();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(email, name, password);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 w-full max-w-sm mx-auto">
      <h2 className="text-2xl font-bold text-center">Register</h2>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <input
        type="text"
        placeholder="Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
        className="w-full p-2 border rounded"
      />
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        className="w-full p-2 border rounded"
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        minLength={8}
        className="w-full p-2 border rounded"
      />
      <button
        type="submit"
        disabled={loading}
        className="w-full p-2 bg-blue-600 text-white rounded disabled:opacity-50"
      >
        {loading ? "Registering..." : "Register"}
      </button>
      <p className="text-center text-sm">
        Already have an account?{" "}
        <button type="button" onClick={onSwitchToLogin} className="text-blue-600 underline">
          Login
        </button>
      </p>
    </form>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/extensions/auth/
git commit -m "feat(frontend): add auth provider, login and register components"
```

---

## Task 13: Frontend — i18n Setup

**Files:**
- Create: `frontend/src/extensions/i18n/locales/en.json`
- Create: `frontend/src/extensions/i18n/locales/tr.json`
- Create: `frontend/src/extensions/i18n/config.ts`
- Create: `frontend/src/extensions/i18n/provider.tsx`

- [ ] **Step 1: Create locale files and provider**

Create `frontend/src/extensions/i18n/locales/en.json`:

```json
{
  "nav": {
    "notebooks": "Notebooks",
    "settings": "Settings",
    "logout": "Logout"
  },
  "auth": {
    "login": "Login",
    "register": "Register",
    "email": "Email",
    "password": "Password",
    "name": "Name",
    "logging_in": "Logging in...",
    "registering": "Registering...",
    "no_account": "Don't have an account?",
    "have_account": "Already have an account?"
  },
  "outputs": {
    "generate": "Generate",
    "study_guide": "Study Guide",
    "faq": "FAQ",
    "timeline": "Timeline",
    "briefing": "Briefing Document",
    "generating": "Generating...",
    "select_type": "Select output type",
    "no_sources": "Add sources to generate outputs"
  },
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "loading": "Loading...",
    "error": "An error occurred"
  }
}
```

Create `frontend/src/extensions/i18n/locales/tr.json`:

```json
{
  "nav": {
    "notebooks": "Not Defterleri",
    "settings": "Ayarlar",
    "logout": "Çıkış"
  },
  "auth": {
    "login": "Giriş Yap",
    "register": "Kayıt Ol",
    "email": "E-posta",
    "password": "Şifre",
    "name": "Ad",
    "logging_in": "Giriş yapılıyor...",
    "registering": "Kayıt olunuyor...",
    "no_account": "Hesabınız yok mu?",
    "have_account": "Zaten hesabınız var mı?"
  },
  "outputs": {
    "generate": "Oluştur",
    "study_guide": "Çalışma Rehberi",
    "faq": "SSS",
    "timeline": "Zaman Çizelgesi",
    "briefing": "Brifing Dokümanı",
    "generating": "Oluşturuluyor...",
    "select_type": "Çıktı türü seçin",
    "no_sources": "Çıktı oluşturmak için kaynak ekleyin"
  },
  "common": {
    "save": "Kaydet",
    "cancel": "İptal",
    "delete": "Sil",
    "loading": "Yükleniyor...",
    "error": "Bir hata oluştu"
  }
}
```

Create `frontend/src/extensions/i18n/config.ts`:

```typescript
export const defaultLocale = "en";

export const supportedLocales = ["en", "tr"] as const;

export type Locale = (typeof supportedLocales)[number];

export function isSupported(locale: string): locale is Locale {
  return supportedLocales.includes(locale as Locale);
}
```

Create `frontend/src/extensions/i18n/provider.tsx`:

```tsx
"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { defaultLocale, isSupported, Locale } from "./config";

import en from "./locales/en.json";
import tr from "./locales/tr.json";

const messages: Record<Locale, Record<string, any>> = { en, tr };

interface I18nContextType {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | null>(null);

export function I18nProvider({ children, initialLocale }: { children: ReactNode; initialLocale?: string }) {
  const [locale, setLocaleState] = useState<Locale>(
    isSupported(initialLocale || "") ? (initialLocale as Locale) : defaultLocale
  );

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    localStorage.setItem("locale", l);
  }, []);

  const t = useCallback(
    (key: string): string => {
      const parts = key.split(".");
      let val: any = messages[locale];
      for (const p of parts) {
        val = val?.[p];
      }
      if (typeof val === "string") return val;
      // Fallback to default locale
      val = messages[defaultLocale];
      for (const p of parts) {
        val = val?.[p];
      }
      return typeof val === "string" ? val : key;
    },
    [locale]
  );

  return <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/extensions/i18n/
git commit -m "feat(frontend): add i18n provider with TR/EN locale support"
```

---

## Task 14: Frontend — Output Panel Components

**Files:**
- Create: `frontend/src/extensions/outputs/output-selector.tsx`
- Create: `frontend/src/extensions/outputs/output-viewer.tsx`
- Create: `frontend/src/extensions/outputs/output-panel.tsx`

- [ ] **Step 1: Create output components**

Create `frontend/src/extensions/outputs/output-selector.tsx`:

```tsx
"use client";

import React, { useEffect, useState } from "react";
import { useI18n } from "../i18n/provider";

interface OutputType {
  name: string;
  title: string;
  description: string;
}

interface Props {
  onSelect: (type: string) => void;
  selected: string | null;
}

export function OutputSelector({ onSelect, selected }: Props) {
  const { t } = useI18n();
  const [types, setTypes] = useState<OutputType[]>([]);

  useEffect(() => {
    fetch("/api/ext/outputs/types")
      .then((r) => r.json())
      .then(setTypes)
      .catch(console.error);
  }, []);

  return (
    <div className="flex gap-2 flex-wrap">
      {types.map((type) => (
        <button
          key={type.name}
          onClick={() => onSelect(type.name)}
          className={`px-3 py-1.5 rounded-md text-sm border transition-colors ${
            selected === type.name
              ? "bg-blue-600 text-white border-blue-600"
              : "bg-white hover:bg-gray-50 border-gray-300"
          }`}
        >
          {t(`outputs.${type.name}`) || type.title}
        </button>
      ))}
    </div>
  );
}
```

Create `frontend/src/extensions/outputs/output-viewer.tsx`:

```tsx
"use client";

import React from "react";

interface Props {
  content: string;
  outputType: string;
}

export function OutputViewer({ content, outputType }: Props) {
  if (!content) return null;

  return (
    <div className="prose prose-sm max-w-none p-4 border rounded-lg bg-white">
      <div dangerouslySetInnerHTML={{ __html: content }} />
    </div>
  );
}
```

Create `frontend/src/extensions/outputs/output-panel.tsx`:

```tsx
"use client";

import React, { useState } from "react";
import { OutputSelector } from "./output-selector";
import { OutputViewer } from "./output-viewer";
import { useI18n } from "../i18n/provider";
import { useAuthContext } from "../auth/auth-provider";

interface Props {
  notebookId: string;
}

export function OutputPanel({ notebookId }: Props) {
  const { t, locale } = useI18n();
  const { accessToken } = useAuthContext();
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    if (!selectedType) return;
    setLoading(true);
    setError("");
    setContent("");

    try {
      const res = await fetch("/api/ext/outputs/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        },
        body: JSON.stringify({
          notebook_id: notebookId,
          output_type: selectedType,
          language: locale,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Generation failed");
      }

      const data = await res.json();
      setContent(data.content);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <OutputSelector onSelect={setSelectedType} selected={selectedType} />
        <button
          onClick={handleGenerate}
          disabled={!selectedType || loading}
          className="px-4 py-1.5 bg-blue-600 text-white rounded-md text-sm disabled:opacity-50"
        >
          {loading ? t("outputs.generating") : t("outputs.generate")}
        </button>
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {content && <OutputViewer content={content} outputType={selectedType || ""} />}
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/extensions/outputs/
git commit -m "feat(frontend): add output panel with selector, viewer, and generation"
```

---

## Task 15: Remote LLM Configuration (Gemma 4)

**Files:**
- No new files needed — uses open-notebook's existing Esperanto/provider config

- [ ] **Step 1: Document the configuration**

open-notebook already supports custom OpenAI-compatible endpoints via its settings UI. To connect to the remote Gemma 4 on H100:

1. Start the Gemma 4 server with an OpenAI-compatible API (vLLM recommended):
```bash
# On the H100 server
python -m vllm.entrypoints.openai.api_server \
  --model google/gemma-4-27b \
  --port 8000 \
  --host 0.0.0.0
```

2. In open-notebook UI → Settings → API Keys, add:
   - Provider: "OpenAI Compatible"
   - Base URL: `http://your-h100-server:8000/v1`
   - API Key: (empty or your key)
   - Model name: `google/gemma-4-27b`

3. Or via `docker-compose.override.yml` environment variables (already created in Task 1):
```yaml
- REMOTE_LLM_BASE_URL=http://your-h100-server:8000/v1
- REMOTE_LLM_MODEL_NAME=google/gemma-4-27b
```

- [ ] **Step 2: Verify connectivity**

Run: `curl http://your-h100-server:8000/v1/models`
Expected: JSON response listing available models including `google/gemma-4-27b`

- [ ] **Step 3: Test chat with remote model**

Open the notebook UI, start a chat, select the remote model, and send a test message.
Expected: Response generated by Gemma 4 on the H100.

- [ ] **Step 4: Commit config documentation**

```bash
git add docker-compose.override.yml
git commit -m "docs: add remote LLM (Gemma 4) connection configuration"
```

---

## Task 16: End-to-End Smoke Test

- [ ] **Step 1: Start all services**

```bash
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d
```

- [ ] **Step 2: Verify API health**

Run: `curl http://localhost:5055/health`
Expected: `{"status":"healthy"}`

- [ ] **Step 3: Test auth flow**

```bash
# Register
curl -X POST http://localhost:5055/api/ext/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"securePass123!"}'

# Login
curl -X POST http://localhost:5055/api/ext/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"securePass123!"}'
```

Expected: Both return `access_token` and `refresh_token`

- [ ] **Step 4: Test output types endpoint**

```bash
curl http://localhost:5055/api/ext/outputs/types \
  -H "Authorization: Bearer <access_token>"
```

Expected: JSON array with study_guide, faq, timeline, briefing

- [ ] **Step 5: Test output generation with a notebook**

```bash
curl -X POST http://localhost:5055/api/ext/outputs/generate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"notebook_id":"notebook:<id>","output_type":"study_guide","language":"tr"}'
```

Expected: JSON with generated study guide content in Turkish

- [ ] **Step 6: Verify i18n**

```bash
# Request with Turkish locale
curl http://localhost:5055/api/ext/outputs/types \
  -H "Authorization: Bearer <access_token>" \
  -H "Accept-Language: tr"
```

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "chore: end-to-end smoke test passed — MVP complete"
```
