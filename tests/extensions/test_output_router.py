import pytest
from unittest.mock import AsyncMock, patch
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
