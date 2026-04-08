"""TSG Report Router testleri — şirket verileri REST endpoint'leri."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from extensions.tsg.report_router import create_tsg_report_router


# ----------------------------------------------------------------
# Test istemcisi kurulumu
# ----------------------------------------------------------------


def make_client(mock_repo_query: AsyncMock) -> TestClient:
    """Router'ı mocked repo_query ile bir FastAPI app'e bağlar."""
    app = FastAPI()
    router = create_tsg_report_router()
    app.include_router(router)
    return TestClient(app)


# ----------------------------------------------------------------
# 1. list_companies — şirket listesi döner
# ----------------------------------------------------------------


@patch(
    "extensions.tsg.report_router.repo_query",
    new_callable=AsyncMock,
)
def test_list_companies_returns_array(mock_query):
    """GET /companies endpoint'i şirketlerin listesini döndürmeli."""
    mock_query.return_value = [
        [
            {"id": "ext_company:abc", "name": "Alfa A.Ş.", "status": "aktif"},
            {"id": "ext_company:def", "name": "Beta Ltd.", "status": "pasif"},
        ]
    ]

    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)

    response = client.get("/companies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "Alfa A.Ş."


# ----------------------------------------------------------------
# 2. get_company_card — şirket + alanlar döner
# ----------------------------------------------------------------


@patch(
    "extensions.tsg.report_router.repo_query",
    new_callable=AsyncMock,
)
def test_get_company_card_returns_company_and_fields(mock_query):
    """GET /companies/{id}/card şirket bilgisi ve alanlarını döndürmeli."""
    mock_query.return_value = [
        [{"id": "ext_company:abc", "name": "Alfa A.Ş.", "status": "aktif"}],
        [
            {"id": "ext_company_field:1", "company_id": "ext_company:abc", "key": "vergi_no", "value": "123456"},
            {"id": "ext_company_field:2", "company_id": "ext_company:abc", "key": "adres", "value": "İstanbul"},
        ],
    ]

    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)

    response = client.get("/companies/abc/card")
    assert response.status_code == 200
    data = response.json()
    assert "company" in data
    assert "fields" in data
    assert data["company"]["name"] == "Alfa A.Ş."
    assert len(data["fields"]) == 2


# ----------------------------------------------------------------
# 3. get_company_card — şirket bulunamadığında 404 döner
# ----------------------------------------------------------------


@patch(
    "extensions.tsg.report_router.repo_query",
    new_callable=AsyncMock,
)
def test_get_company_card_returns_404_when_not_found(mock_query):
    """Şirket bulunamadığında 404 HTTP hatası dönmeli."""
    mock_query.return_value = [
        [],   # şirket yok
        [],   # alan yok
    ]

    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)

    response = client.get("/companies/bilinmeyen/card")
    assert response.status_code == 404
    assert "bulunamadı" in response.json()["detail"].lower()


# ----------------------------------------------------------------
# 4. get_company_timeline — olayları döner
# ----------------------------------------------------------------


@patch(
    "extensions.tsg.report_router.repo_query",
    new_callable=AsyncMock,
)
def test_get_company_timeline_returns_events(mock_query):
    """GET /companies/{id}/timeline şirket olaylarını döndürmeli."""
    mock_query.return_value = [
        [
            {
                "id": "ext_company_event:1",
                "company_id": "ext_company:abc",
                "event_type": "kuruluş",
                "gazette_date": "2020-01-15",
            },
            {
                "id": "ext_company_event:2",
                "company_id": "ext_company:abc",
                "event_type": "sermaye_artırımı",
                "gazette_date": "2022-06-10",
            },
        ]
    ]

    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)

    response = client.get("/companies/abc/timeline")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["event_type"] == "kuruluş"


# ----------------------------------------------------------------
# 5. get_company_persons — filtrelenmiş kişi listesi döner
# ----------------------------------------------------------------


@patch(
    "extensions.tsg.report_router.repo_query",
    new_callable=AsyncMock,
)
def test_get_company_persons_returns_filtered_list(mock_query):
    """GET /companies/{id}/persons kişileri döndürmeli ve person_type filtresi çalışmalı."""
    mock_query.return_value = [
        [
            {
                "id": "ext_company_person:1",
                "company_id": "ext_company:abc",
                "name": "Ahmet Yılmaz",
                "person_type": "yönetici",
                "is_active": True,
                "imza_derecesi": 1,
            },
            {
                "id": "ext_company_person:2",
                "company_id": "ext_company:abc",
                "name": "Mehmet Demir",
                "person_type": "ortak",
                "is_active": True,
                "imza_derecesi": 2,
            },
        ]
    ]

    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)

    # person_type filtresi ile yöneticileri sorgula
    response = client.get("/companies/abc/persons?person_type=yönetici")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Ahmet Yılmaz"
    assert data[0]["person_type"] == "yönetici"
