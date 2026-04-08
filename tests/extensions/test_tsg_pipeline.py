"""TSG Pipeline testleri — splitter → extractor → state_manager tam akış."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import extensions.tsg.pipeline as pipeline_module
from extensions.tsg.pipeline import process_gazette_file


# ----------------------------------------------------------------
# Yardımcı: her test öncesi _processed_hashes setini temizle
# ----------------------------------------------------------------


@pytest.fixture(autouse=True)
def clear_processed_hashes():
    """Her testten önce hash setini temizle (yalıtım sağlar)."""
    pipeline_module._processed_hashes.clear()
    yield
    pipeline_module._processed_hashes.clear()


# ----------------------------------------------------------------
# Geçerli gazete metni (testlerde ortak kullanım)
# ----------------------------------------------------------------

VALID_TEXT = (
    "21 HAZİRAN 2024 SAYI : 11106\n"
    "T.C. İSTANBUL TİCARET SİCİLİ MÜDÜRLÜĞÜ\n"
    "Ticaret Unvanı: Test Teknoloji A.Ş.\n"
    "Sermaye: 50.000 TL\n"
    "MERSİS No: 0123456789012345\n"
    "Açıklama: Kuruluş ilanı detayları burada yer almaktadır.\n"
)


# ----------------------------------------------------------------
# Test 1 — Başarılı tam akış
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.pipeline.add_company_event", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.update_company_persons", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.update_company_fields", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.update_company_meta", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.find_or_create_company", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.detail_extract", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.triage_extract", new_callable=AsyncMock)
async def test_full_pipeline_success(
    mock_triage,
    mock_detail,
    mock_find_or_create,
    mock_update_meta,
    mock_update_fields,
    mock_update_persons,
    mock_add_event,
):
    """Tam akış başarılı şekilde tamamlanmalı ve tüm state_manager fonksiyonları çağrılmalı."""
    # Triage sonucu
    mock_triage.return_value = {
        "islem_turu": "kurulus",
        "gazette_date": "2024-06-21",
        "gazette_no": "11106",
        "ilan_kodu": "A-001",
        "sirket_unvani": "Test Teknoloji A.Ş.",
        "mersis_no": "0123456789012345",
    }

    # Detay sonucu
    mock_detail.return_value = {
        "fields": [
            {"field_type": "sermaye", "value": "50000", "new_value": "50000"}
        ],
        "persons": [
            {"ad_soyad": "Ali Veli", "person_type": "yonetim", "unvan": "Müdür"}
        ],
        "events": [],
        "articles": [],
        "delil_belgesi": None,
    }

    # find_or_create_company
    mock_find_or_create.return_value = "ext_company:test123"

    result = await process_gazette_file(
        text=VALID_TEXT,
        company_name="Test Teknoloji A.Ş.",
        source_id="source:abc",
    )

    # Başarı kontrolü
    assert result["success"] is True
    assert result["company_id"] == "ext_company:test123"
    assert result["event_type"] == "kurulus"
    assert result["gazette_date"] == "2024-06-21"
    assert result["gazette_no"] == "11106"

    # Tüm state_manager fonksiyonları çağrıldı mı?
    mock_find_or_create.assert_called_once_with(
        name="Test Teknoloji A.Ş.",
        mersis_no="0123456789012345",
    )
    mock_update_meta.assert_called_once()
    mock_update_fields.assert_called_once()
    mock_update_persons.assert_called_once()
    mock_add_event.assert_called_once()


# ----------------------------------------------------------------
# Test 2 — Geçersiz içerik
# ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_content_returns_failure():
    """Geçersiz dosya içeriği success=False döndürmeli."""
    result = await process_gazette_file(
        text="kısa metin",
        company_name="Herhangi Şirket A.Ş.",
    )

    assert result["success"] is False
    assert result["error"] == "Geçersiz dosya içeriği"


# ----------------------------------------------------------------
# Test 3 — Şirket ilanı bulunamıyor
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.pipeline.triage_extract", new_callable=AsyncMock)
async def test_company_not_found_returns_failure(mock_triage):
    """Şirket ilanı bulunamadığında success=False döndürmeli."""
    # Triage çağrılmamalı
    result = await process_gazette_file(
        text=VALID_TEXT,
        company_name="Bambaşka Şirket Ltd. Şti.",
    )

    assert result["success"] is False
    assert "bulunamadı" in result["error"].lower() or "success" not in result or not result["success"]
    # Triage LLM çağrısı yapılmamış olmalı
    mock_triage.assert_not_called()


# ----------------------------------------------------------------
# Test 4 — Duplicate dosya tespiti
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.pipeline.add_company_event", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.update_company_persons", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.update_company_fields", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.update_company_meta", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.find_or_create_company", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.detail_extract", new_callable=AsyncMock)
@patch("extensions.tsg.pipeline.triage_extract", new_callable=AsyncMock)
async def test_duplicate_file_returns_failure(
    mock_triage,
    mock_detail,
    mock_find_or_create,
    mock_update_meta,
    mock_update_fields,
    mock_update_persons,
    mock_add_event,
):
    """Aynı dosya iki kez gönderildiğinde ikincisi duplicate hatası döndürmeli."""
    mock_triage.return_value = {
        "islem_turu": "kurulus",
        "gazette_date": "2024-06-21",
        "gazette_no": "11106",
        "ilan_kodu": "A-001",
        "sirket_unvani": "Test Teknoloji A.Ş.",
        "mersis_no": "0123456789012345",
    }
    mock_detail.return_value = {
        "fields": [],
        "persons": [],
        "events": [],
        "articles": [],
        "delil_belgesi": None,
    }
    mock_find_or_create.return_value = "ext_company:test123"

    # İlk çağrı başarılı olmalı
    first_result = await process_gazette_file(
        text=VALID_TEXT,
        company_name="Test Teknoloji A.Ş.",
    )
    assert first_result["success"] is True

    # İkinci çağrı duplicate hatası vermeli
    second_result = await process_gazette_file(
        text=VALID_TEXT,
        company_name="Test Teknoloji A.Ş.",
    )
    assert second_result["success"] is False
    assert second_result["error"] == "Duplicate dosya"
