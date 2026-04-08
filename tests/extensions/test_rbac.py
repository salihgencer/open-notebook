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
    request.state = MagicMock(spec=[])
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
