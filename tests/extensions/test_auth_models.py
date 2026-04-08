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
