"""TSG LLM Extractor testleri — triage ve detay çıkarım fonksiyonları."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from extensions.tsg.extractor import (
    detail_extract,
    load_prompt,
    parse_json_response,
    triage_extract,
)


# ----------------------------------------------------------------
# load_prompt testleri
# ----------------------------------------------------------------


def test_load_prompt_triage_returns_string():
    """triage prompt dosyası yüklendiğinde string döndürmeli."""
    prompt = load_prompt("triage")
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_load_prompt_genel_returns_string():
    """genel prompt dosyası yüklendiğinde string döndürmeli."""
    prompt = load_prompt("genel")
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_load_prompt_triage_contains_text_placeholder():
    """triage prompt'u {text} yer tutucusunu içermeli."""
    prompt = load_prompt("triage")
    assert "{text}" in prompt


def test_load_prompt_genel_contains_placeholders():
    """genel prompt'u {text} ve {islem_turu} yer tutucularını içermeli."""
    prompt = load_prompt("genel")
    assert "{text}" in prompt
    assert "{islem_turu}" in prompt


def test_load_prompt_raises_for_nonexistent():
    """Var olmayan prompt dosyası FileNotFoundError fırlatmalı."""
    with pytest.raises(FileNotFoundError):
        load_prompt("var_olmayan_prompt_xyz")


# ----------------------------------------------------------------
# parse_json_response testleri
# ----------------------------------------------------------------


def test_parse_json_response_clean_json():
    """Temiz JSON metni doğru ayrıştırılmalı."""
    text = '{"islem_turu": "kurulus", "sirket_unvani": "Test A.Ş."}'
    result = parse_json_response(text)
    assert result["islem_turu"] == "kurulus"
    assert result["sirket_unvani"] == "Test A.Ş."


def test_parse_json_response_markdown_wrapped():
    """Markdown kod bloğu içindeki JSON doğru ayrıştırılmalı."""
    text = '```json\n{"islem_turu": "tasfiye", "gazette_no": "1234"}\n```'
    result = parse_json_response(text)
    assert result["islem_turu"] == "tasfiye"
    assert result["gazette_no"] == "1234"


def test_parse_json_response_markdown_no_lang():
    """Dil belirtilmemiş markdown kod bloğu da ayrıştırılmalı."""
    text = '```\n{"fields": [], "persons": []}\n```'
    result = parse_json_response(text)
    assert result["fields"] == []
    assert result["persons"] == []


def test_parse_json_response_json_embedded_in_text():
    """Metin içine gömülü JSON doğru çıkarılmalı."""
    text = 'İşte sonuç: {"islem_turu": "sermaye", "mersis_no": "123456"} - bu JSON\'dur.'
    result = parse_json_response(text)
    assert result["islem_turu"] == "sermaye"
    assert result["mersis_no"] == "123456"


def test_parse_json_response_raises_for_invalid():
    """Geçersiz JSON içeren metin ValueError fırlatmalı."""
    with pytest.raises(ValueError):
        parse_json_response("Bu hiç JSON içermiyor.")


def test_parse_json_response_raises_for_empty():
    """Boş metin ValueError fırlatmalı."""
    with pytest.raises(ValueError):
        parse_json_response("")


# ----------------------------------------------------------------
# triage_extract testleri
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.extractor.call_llm", new_callable=AsyncMock)
async def test_triage_extract_returns_dict(mock_call_llm):
    """triage_extract dict döndürmeli."""
    mock_call_llm.return_value = json.dumps({
        "islem_turu": "kurulus",
        "gazette_date": "2024-01-15",
        "gazette_no": "10987",
        "ilan_kodu": "A-12345",
        "sirket_unvani": "Örnek Teknoloji A.Ş.",
        "mersis_no": "0123456789012345",
    })

    result = await triage_extract("Test ilan metni...")

    assert isinstance(result, dict)
    assert result["islem_turu"] == "kurulus"
    assert result["gazette_date"] == "2024-01-15"
    assert result["gazette_no"] == "10987"
    assert result["ilan_kodu"] == "A-12345"
    assert result["sirket_unvani"] == "Örnek Teknoloji A.Ş."
    assert result["mersis_no"] == "0123456789012345"


@pytest.mark.asyncio
@patch("extensions.tsg.extractor.call_llm", new_callable=AsyncMock)
async def test_triage_extract_calls_llm_with_text(mock_call_llm):
    """triage_extract, ilan metnini prompt içine yerleştirmeli."""
    ilan_metni = "ÖRNEK İLAN METNİ BURAYA"
    mock_call_llm.return_value = '{"islem_turu": "diger"}'

    await triage_extract(ilan_metni)

    # call_llm çağrıldı mı kontrol et
    mock_call_llm.assert_called_once()
    # Prompt içinde ilan metni var mı
    call_args = mock_call_llm.call_args[0][0]
    assert ilan_metni in call_args


@pytest.mark.asyncio
@patch("extensions.tsg.extractor.call_llm", new_callable=AsyncMock)
async def test_triage_extract_handles_markdown_response(mock_call_llm):
    """triage_extract, markdown sarmalı LLM yanıtını işleyebilmeli."""
    mock_call_llm.return_value = '```json\n{"islem_turu": "adres", "gazette_no": "5555"}\n```'

    result = await triage_extract("Adres değişikliği ilanı...")

    assert result["islem_turu"] == "adres"
    assert result["gazette_no"] == "5555"


# ----------------------------------------------------------------
# detail_extract testleri
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.extractor.call_llm", new_callable=AsyncMock)
async def test_detail_extract_returns_dict(mock_call_llm):
    """detail_extract dict döndürmeli."""
    mock_call_llm.return_value = json.dumps({
        "fields": [
            {
                "field_type": "sermaye",
                "field_name": "Sermaye",
                "old_value": "100000",
                "new_value": "500000",
                "currency": "TRY",
                "notes": None,
            }
        ],
        "persons": [
            {
                "ad_soyad": "Ahmet Yılmaz",
                "person_type": "yonetim",
                "unvan": "Genel Müdür",
                "tc_kimlik": None,
                "uyruk": "Türk",
                "pay_orani": None,
                "pay_tutari": None,
                "yetki": "tek başına",
                "is_active": True,
            }
        ],
        "events": [],
        "articles": [],
        "delil_belgesi": None,
    })

    result = await detail_extract("Sermaye artırımı ilanı...", "sermaye")

    assert isinstance(result, dict)
    assert "fields" in result
    assert "persons" in result
    assert "events" in result
    assert "articles" in result
    assert "delil_belgesi" in result
    assert len(result["fields"]) == 1
    assert result["fields"][0]["field_type"] == "sermaye"
    assert result["persons"][0]["ad_soyad"] == "Ahmet Yılmaz"


@pytest.mark.asyncio
@patch("extensions.tsg.extractor.call_llm", new_callable=AsyncMock)
async def test_detail_extract_uses_genel_fallback(mock_call_llm):
    """detail_extract, türe özgü prompt yoksa genel prompt kullanmalı."""
    mock_call_llm.return_value = json.dumps({
        "fields": [],
        "persons": [],
        "events": [],
        "articles": [],
        "delil_belgesi": None,
    })

    # "ttk198" için özel prompt yok, genel.yaml kullanılmalı
    result = await detail_extract("TTK 198 ilanı...", "ttk198")

    assert isinstance(result, dict)
    mock_call_llm.assert_called_once()
    # Genel prompt {islem_turu} içerdiğinden, prompt'ta islem_turu değeri olmalı
    call_args = mock_call_llm.call_args[0][0]
    assert "ttk198" in call_args


@pytest.mark.asyncio
@patch("extensions.tsg.extractor.call_llm", new_callable=AsyncMock)
async def test_detail_extract_includes_text_in_prompt(mock_call_llm):
    """detail_extract, ilan metnini prompt içine yerleştirmeli."""
    ilan_metni = "DETAY İLAN METNİ TEST"
    mock_call_llm.return_value = '{"fields": [], "persons": [], "events": [], "articles": [], "delil_belgesi": null}'

    await detail_extract(ilan_metni, "yonetim")

    mock_call_llm.assert_called_once()
    call_args = mock_call_llm.call_args[0][0]
    assert ilan_metni in call_args
