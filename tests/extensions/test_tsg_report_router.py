"""TSG Report Router testleri."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from extensions.tsg.report_router import create_tsg_report_router


@patch("extensions.tsg.report_router.repo_query", new_callable=AsyncMock)
def test_list_companies_returns_array(mock_query):
    mock_query.return_value = [
        {"id": "ext_company:abc", "unvan": "Alfa A.Ş.", "status": "aktif", "gazette_count": 5},
        {"id": "ext_company:def", "unvan": "Beta Ltd.", "status": "pasif", "gazette_count": 3},
    ]
    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)
    response = client.get("/companies")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] == "Alfa A.Ş."


@patch("extensions.tsg.report_router.repo_query", new_callable=AsyncMock)
def test_get_company_card(mock_query):
    mock_query.side_effect = [
        [{"id": "ext_company:abc", "unvan": "Alfa A.Ş.", "mersis_no": "123", "gazette_count": 5}],
        [{"id": "f:1", "field_type": "sermaye", "value": "50M", "gazette_date": "2024-01-01"}],
    ]
    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)
    response = client.get("/companies/ext_company:abc/card")
    assert response.status_code == 200
    data = response.json()
    assert data["company"]["name"] == "Alfa A.Ş."
    assert len(data["fields"]) == 1
    assert data["fields"][0]["value"] == "50M"


@patch("extensions.tsg.report_router.repo_query", new_callable=AsyncMock)
def test_get_company_card_404(mock_query):
    mock_query.side_effect = [[], []]
    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)
    response = client.get("/companies/ext_company:xxx/card")
    assert response.status_code == 404


@patch("extensions.tsg.report_router.repo_query", new_callable=AsyncMock)
def test_get_company_timeline(mock_query):
    mock_query.return_value = [
        {"id": "e:1", "event_type": "kurulus", "aciklama": "Şirket kuruldu", "gazette_date": "2020-01-15"},
    ]
    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)
    response = client.get("/companies/ext_company:abc/timeline")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["event_type"] == "kurulus"
    assert data[0]["summary"] == "Şirket kuruldu"


@patch("extensions.tsg.report_router.repo_query", new_callable=AsyncMock)
def test_get_company_persons(mock_query):
    mock_query.return_value = [
        {"id": "p:1", "ad_soyad": "Ahmet Yılmaz", "person_type": "yonetim", "is_active": True},
        {"id": "p:2", "ad_soyad": "Mehmet Demir", "person_type": "ortak", "is_active": True},
    ]
    app = FastAPI()
    app.include_router(create_tsg_report_router())
    client = TestClient(app)
    response = client.get("/companies/ext_company:abc/persons?person_type=yonetim")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Ahmet Yılmaz"
