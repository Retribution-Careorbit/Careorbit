from types import SimpleNamespace

import pytest

import api.middleware.auth as auth_mod
import api.routes.chat as chat_mod
from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


async def _fake_user(_request):
    return {"id": "patient-id", "tier": "free"}


@pytest.fixture(autouse=True)
def _patch_auth(monkeypatch):
    monkeypatch.setattr(auth_mod, "get_current_user", _fake_user)


def test_chat_query_includes_translation_and_safety_metadata(monkeypatch):
    async def _fake_process_query(patient_id, message, language):
        return SimpleNamespace(
            message="safe response",
            language=language,
            agents_used=["medication_agent"],
            alerts=[],
            care_gaps=[],
            recommendations=[],
            confidence=0.81,
            response_metadata={
                "translation_used": True,
                "source_language": "hi",
                "safety_interventions_applied": ["roundtrip_drift_fallback"],
                "confidence_warning": "translation_semantic_drift",
            },
        )

    monkeypatch.setattr(chat_mod.orchestrator, "process_query", _fake_process_query)

    response = client.post("/api/chat/query", json={"message": "Meri dawa", "language": "hi"})
    assert response.status_code == 200
    body = response.json()

    assert body["degraded_mode"] is False
    assert body["translation_used"] is True
    assert body["source_language"] == "hi"
    assert body["safety_interventions_applied"] == ["roundtrip_drift_fallback"]
    assert body["confidence_warning"] == "translation_semantic_drift"


def test_chat_query_degraded_mode_keeps_metadata_fields(monkeypatch):
    async def _fail_process_query(patient_id, message, language):
        raise RuntimeError("orchestrator failure")

    async def _fake_grounded_response(patient_id, message, language):
        return SimpleNamespace(
            message="grounded fallback",
            language=language,
            agents_used=["history_agent"],
            alerts=[],
            care_gaps=[],
            recommendations=[],
            confidence=0.72,
            response_metadata={
                "translation_used": False,
                "source_language": "en",
                "safety_interventions_applied": [],
                "confidence_warning": None,
            },
        )

    monkeypatch.setattr(chat_mod.orchestrator, "process_query", _fail_process_query)
    monkeypatch.setattr(chat_mod.orchestrator, "build_grounded_response", _fake_grounded_response)

    response = client.post("/api/chat/query", json={"message": "How am I doing?", "language": "en"})
    assert response.status_code == 200
    body = response.json()

    assert body["degraded_mode"] is True
    assert body["translation_used"] is False
    assert body["source_language"] == "en"
    assert body["safety_interventions_applied"] == []
    assert body["confidence_warning"] is None


def test_chat_query_defaults_metadata_when_orchestrator_has_no_response_metadata(monkeypatch):
    async def _fake_process_query(patient_id, message, language):
        return SimpleNamespace(
            message="response without metadata",
            language=language,
            agents_used=[],
            alerts=[],
            care_gaps=[],
            recommendations=[],
            confidence=0.70,
        )

    monkeypatch.setattr(chat_mod.orchestrator, "process_query", _fake_process_query)

    response = client.post("/api/chat/query", json={"message": "Hello", "language": "en"})
    assert response.status_code == 200
    body = response.json()

    assert body["translation_used"] is False
    assert body["source_language"] == "en"
    assert body["safety_interventions_applied"] == []
    assert body["confidence_warning"] is None


def test_chat_query_returns_503_with_dependency_contract(monkeypatch):
    failures = [
        {
            "service": "azure_translator",
            "operation": "translate_to_english",
            "reason": "Translator unavailable for non-English request",
        }
    ]

    async def _dependency_unavailable(patient_id, message, language):
        raise chat_mod.AzureDependencyUnavailable(failures)

    monkeypatch.setattr(chat_mod.orchestrator, "process_query", _dependency_unavailable)

    response = client.post("/api/chat/query", json={"message": "Meri dawa", "language": "hi"})
    assert response.status_code == 503
    body = response.json()

    assert "detail" in body
    detail = body["detail"]
    assert detail["error"] == "azure_dependencies_unavailable"
    assert isinstance(detail.get("trace_id"), str) and detail["trace_id"]
    assert detail["degraded_mode"] is False
    assert isinstance(detail["dependencies"], list)
    assert detail["dependencies"][0]["service"] == "azure_translator"
