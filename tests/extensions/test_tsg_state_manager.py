"""TSG State Manager testleri — şirket veri güncelleme fonksiyonları."""

from unittest.mock import AsyncMock, patch

import pytest

from extensions.tsg.state_manager import (
    add_company_event,
    find_or_create_company,
    update_company_fields,
    update_company_meta,
    update_company_persons,
)


# ----------------------------------------------------------------
# 1. find_or_create_company — yeni kayıt oluşturma
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_create", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
async def test_find_or_create_company_creates_new_when_not_found(
    mock_query, mock_create
):
    """Şirket bulunamadığında yeni kayıt oluşturulmalı."""
    # İsim ve mersis araması boş döner
    mock_query.return_value = [[]]

    mock_create.return_value = {"id": "ext_company:new123", "unvan": "Test AŞ"}

    company_id = await find_or_create_company(
        name="Test AŞ", mersis_no="1234567890"
    )

    assert company_id == "ext_company:new123"
    mock_create.assert_called_once()
    create_call_args = mock_create.call_args
    assert create_call_args[0][0] == "ext_company"
    assert create_call_args[0][1]["unvan"] == "Test AŞ"
    assert create_call_args[0][1]["mersis_no"] == "1234567890"


# ----------------------------------------------------------------
# 2. find_or_create_company — mevcut kayıt bulma (mersis ile)
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_create", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
async def test_find_or_create_company_finds_existing_by_mersis(
    mock_query, mock_create
):
    """Mersis no ile mevcut şirket bulunduğunda yeni kayıt oluşturulmamalı."""
    mock_query.return_value = [[{"id": "ext_company:existing456", "unvan": "Var Olan AŞ", "mersis_no": "9876543210"}]]

    company_id = await find_or_create_company(
        name="Var Olan AŞ", mersis_no="9876543210"
    )

    assert company_id == "ext_company:existing456"
    mock_create.assert_not_called()


# ----------------------------------------------------------------
# 3. update_company_fields — yeni alan oluşturma
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_create", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_update", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
async def test_update_company_fields_creates_new_field(
    mock_query, mock_update, mock_create
):
    """Mevcut alan yoksa yeni kayıt oluşturulmalı."""
    # Mevcut alan yok
    mock_query.return_value = [[]]
    mock_create.return_value = {"id": "ext_company_field:field1"}

    await update_company_fields(
        company_id="ext_company:abc123",
        fields={"sermaye": {"value": "50.000 TL"}},
        gazette_date="2024-03-15",
        gazette_no="9876",
    )

    mock_create.assert_called_once()
    create_call_args = mock_create.call_args
    assert create_call_args[0][0] == "ext_company_field"
    data = create_call_args[0][1]
    assert data["field_type"] == "sermaye"
    assert data["value"] == "50.000 TL"
    assert data["gazette_date"] == "2024-03-15"
    mock_update.assert_not_called()


# ----------------------------------------------------------------
# 4. update_company_fields — daha yeni tarihle güncelleme
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_create", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_update", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
async def test_update_company_fields_updates_when_newer_date(
    mock_query, mock_update, mock_create
):
    """Yeni tarih mevcut tarihten büyükse alan güncellenmeli."""
    existing_field = {
        "id": "ext_company_field:field1",
        "field_type": "sermaye",
        "value": "50.000 TL",
        "gazette_date": "2023-01-10",
        "company_id": "ext_company:abc123",
    }
    mock_query.return_value = [[existing_field]]

    await update_company_fields(
        company_id="ext_company:abc123",
        fields={"sermaye": {"value": "100.000 TL"}},
        gazette_date="2024-06-20",
    )

    mock_update.assert_called_once()
    update_call_args = mock_update.call_args
    data = update_call_args[0][2]
    assert data["value"] == "100.000 TL"
    assert data["gazette_date"] == "2024-06-20"
    mock_create.assert_not_called()


# ----------------------------------------------------------------
# 5. update_company_fields — eski tarihle atlama (KRİTİK TEST)
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_create", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_update", new_callable=AsyncMock)
@patch("extensions.tsg.state_manager.repo_query", new_callable=AsyncMock)
async def test_update_company_fields_skips_when_older_date(
    mock_query, mock_update, mock_create
):
    """Yeni tarih mevcut tarihten küçük veya eşitse güncelleme YAPILMAMALI."""
    existing_field = {
        "id": "ext_company_field:field1",
        "field_type": "adres",
        "value": "Yeni Adres Cad. No:1",
        "gazette_date": "2024-12-01",  # daha yeni tarih
        "company_id": "ext_company:abc123",
    }
    mock_query.return_value = [[existing_field]]

    await update_company_fields(
        company_id="ext_company:abc123",
        fields={"adres": {"value": "Eski Adres Sok. No:5"}},
        gazette_date="2024-01-15",  # daha eski tarih
    )

    # Ne create ne de update çağrılmamalı
    mock_create.assert_not_called()
    mock_update.assert_not_called()


# ----------------------------------------------------------------
# 6. add_company_event — olay kaydı oluşturma
# ----------------------------------------------------------------


@pytest.mark.asyncio
@patch("extensions.tsg.state_manager.repo_create", new_callable=AsyncMock)
async def test_add_company_event_creates_record(mock_create):
    """add_company_event yeni ext_company_event kaydı oluşturmalı ve ID döndürmeli."""
    mock_create.return_value = {
        "id": "ext_company_event:event789",
        "company_id": "ext_company:abc123",
        "event_type": "sermaye",
    }

    event_id = await add_company_event(
        company_id="ext_company:abc123",
        event_type="sermaye",
        summary="Sermaye artışı 100.000 TL'den 200.000 TL'ye çıkarıldı.",
        gazette_date="2024-05-10",
        gazette_no="5432",
    )

    assert event_id == "ext_company_event:event789"
    mock_create.assert_called_once()
    create_call_args = mock_create.call_args
    assert create_call_args[0][0] == "ext_company_event"
    data = create_call_args[0][1]
    assert data["company_id"] == "ext_company:abc123"
    assert data["event_type"] == "sermaye"
    assert data["aciklama"] == "Sermaye artışı 100.000 TL'den 200.000 TL'ye çıkarıldı."
    assert data["gazette_date"] == "2024-05-10"
    assert data["gazette_issue"] == "5432"
