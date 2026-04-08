import os
import pytest

from extensions.i18n.service import I18nService


@pytest.fixture
def i18n():
    locales_dir = os.path.join(os.path.dirname(__file__), "../../extensions/i18n/locales")
    return I18nService(locales_dir=locales_dir, default_locale="en")


def test_translate_english(i18n):
    result = i18n.t("auth.login_success", locale="en")
    assert isinstance(result, str)
    assert len(result) > 0
    assert result == "Login successful"


def test_translate_turkish(i18n):
    result = i18n.t("auth.login_success", locale="tr")
    assert result == "Giriş başarılı"
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
