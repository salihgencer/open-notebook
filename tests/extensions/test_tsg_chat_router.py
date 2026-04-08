"""TSG Chat Router testleri — soru sınıflandırma ve yönlendirme."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from extensions.tsg.chat_router import (
    ChatRequest,
    ChatResponse,
    create_tsg_chat_router,
)


# ----------------------------------------------------------------
# Yardımcı: test client oluştur
# ----------------------------------------------------------------


def make_app() -> FastAPI:
    app = FastAPI()
    app.include_router(create_tsg_chat_router())
    return app


# ----------------------------------------------------------------
# 1. Faktüel soru → answer_factual'a yönlendirilmeli
# ----------------------------------------------------------------


@patch("extensions.tsg.chat_router.answer_factual", new_callable=AsyncMock)
@patch("extensions.tsg.chat_router.classify_question", new_callable=AsyncMock)
def test_factual_question_routes_to_answer_factual(mock_classify, mock_answer_factual):
    """Faktüel soru tipi answer_factual fonksiyonuna yönlendirilmeli."""
    mock_classify.return_value = {
        "type": "factual",
        "company_id": "abc",
        "field": "sermaye",
        "event_type": "null",
        "detail": "sermaye bilgisi",
    }
    mock_answer_factual.return_value = {
        "answer": "Sermaye: 100.000 TL",
        "source": "2023-01-15, Sayı: 12345",
        "type": "db",
    }

    app = make_app()
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"question": "Şirketin sermayesi nedir?", "company_id": "abc"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Sermaye: 100.000 TL"
    assert data["answer_type"] == "db"
    assert data["company_id"] == "abc"

    mock_answer_factual.assert_called_once_with("abc", "sermaye")


# ----------------------------------------------------------------
# 2. Zaman çizelgesi sorusu → answer_timeline'a yönlendirilmeli
# ----------------------------------------------------------------


@patch("extensions.tsg.chat_router.answer_timeline", new_callable=AsyncMock)
@patch("extensions.tsg.chat_router.classify_question", new_callable=AsyncMock)
def test_timeline_question_routes_to_answer_timeline(mock_classify, mock_answer_timeline):
    """Zaman çizelgesi sorusu answer_timeline fonksiyonuna yönlendirilmeli."""
    mock_classify.return_value = {
        "type": "timeline",
        "company_id": "abc",
        "field": "null",
        "event_type": "sermaye",
        "detail": "sermaye değişim geçmişi",
    }
    mock_answer_timeline.return_value = {
        "answer": "• 2020-01-15 — kuruluş\n• 2022-06-10 — sermaye artırımı",
        "source": "2 gazete kaydından",
        "type": "db",
    }

    app = make_app()
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"question": "Şirketin sermaye geçmişi nedir?", "company_id": "abc"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "kuruluş" in data["answer"]
    assert data["answer_type"] == "db"
    assert data["source"] == "2 gazete kaydından"

    mock_answer_timeline.assert_called_once_with("abc", "sermaye")


# ----------------------------------------------------------------
# 3. Yanıt answer_type alanını içermeli
# ----------------------------------------------------------------


@patch("extensions.tsg.chat_router.answer_analytic", new_callable=AsyncMock)
@patch("extensions.tsg.chat_router.classify_question", new_callable=AsyncMock)
def test_response_includes_answer_type(mock_classify, mock_answer_analytic):
    """Her yanıt answer_type alanını içermeli."""
    mock_classify.return_value = {
        "type": "analytic",
        "company_id": "xyz",
        "field": "null",
        "event_type": "null",
        "detail": "genel analiz",
    }
    mock_answer_analytic.return_value = {
        "answer": "Şirket son iki yılda büyümüş görünüyor.",
        "source": "5 alan, 3 olay kaydından",
        "type": "llm",
    }

    app = make_app()
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"question": "Şirket son iki yılda nasıl gelişti?", "company_id": "xyz"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer_type" in data
    assert data["answer_type"] == "llm"
    assert data["company_id"] == "xyz"


# ----------------------------------------------------------------
# 4. Şirket ID yoksa hata mesajı döner
# ----------------------------------------------------------------


@patch("extensions.tsg.chat_router.classify_question", new_callable=AsyncMock)
def test_missing_company_id_returns_error_message(mock_classify):
    """Şirket ID belirtilmemişse anlamlı hata mesajı dönmeli."""
    mock_classify.return_value = {
        "type": "factual",
        "company_id": None,
        "field": "adres",
        "event_type": "null",
        "detail": "adres bilgisi",
    }

    app = make_app()
    client = TestClient(app)

    response = client.post(
        "/chat",
        json={"question": "Adres nedir?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer_type"] == "error"
    assert "şirket" in data["answer"].lower()


# ----------------------------------------------------------------
# 5. ChatResponse modeli doğru alanları içermeli
# ----------------------------------------------------------------


def test_chat_response_model_fields():
    """ChatResponse Pydantic modeli gerekli alanları içermeli."""
    resp = ChatResponse(
        answer="Test yanıtı",
        answer_type="db",
        source="2023-01-01",
        company_id="test123",
    )
    assert resp.answer == "Test yanıtı"
    assert resp.answer_type == "db"
    assert resp.source == "2023-01-01"
    assert resp.company_id == "test123"


def test_chat_response_optional_fields():
    """ChatResponse'da opsiyonel alanlar None olabilmeli."""
    resp = ChatResponse(answer="Yanıt", answer_type="llm")
    assert resp.source is None
    assert resp.company_id is None
