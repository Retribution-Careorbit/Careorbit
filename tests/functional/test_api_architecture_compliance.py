import config as config_mod
import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


async def _fake_user(_request):
    return {"id": "patient-id", "tier": "free"}


async def _allow_access(*_args, **_kwargs):
    return True


def _set_common_env(monkeypatch, *, environment: str, postgres: bool = False):
    monkeypatch.setenv("ENVIRONMENT", environment)
    monkeypatch.setenv("AZURE_KEYVAULT_URI", "")
    monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "")
    monkeypatch.setenv("AZURE_DI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_DI_KEY", "")
    monkeypatch.setenv("AZURE_LANGUAGE_ENDPOINT", "")
    monkeypatch.setenv("AZURE_LANGUAGE_KEY", "")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "")
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "")
    monkeypatch.setenv("AZURE_SEARCH_KEY", "")
    monkeypatch.setenv("AZURE_TRANSLATOR_ENDPOINT", "")
    monkeypatch.setenv("AZURE_TRANSLATOR_KEY", "")
    monkeypatch.setenv("AZURE_COMM_CONNECTION_STRING", "")
    if postgres:
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost:5432/careorbit")
    else:
        monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./careorbit.db")


class TestArchitectureCompliance:
    def test_dev_mode_reports_followed_with_degraded_warnings(self, monkeypatch):
        monkeypatch.setattr(auth_mod, "get_current_user", _fake_user)
        monkeypatch.setattr(rbac_mod, "verify_patient_access", _allow_access)
        _set_common_env(monkeypatch, environment="development", postgres=False)
        config_mod._settings = None

        response = client.get("/api/system/architecture/compliance")
        assert response.status_code == 200
        data = response.json()

        assert data["strict_managed_mode"] is False
        assert data["architecture_followed"] is True
        assert data["degraded_mode"] is True
        assert data["gaps"] == []
        assert len(data["warnings"]) > 0

    def test_production_mode_reports_hard_gaps(self, monkeypatch):
        monkeypatch.setattr(auth_mod, "get_current_user", _fake_user)
        monkeypatch.setattr(rbac_mod, "verify_patient_access", _allow_access)
        _set_common_env(monkeypatch, environment="production", postgres=False)
        config_mod._settings = None

        response = client.get("/api/system/architecture/compliance")
        assert response.status_code == 200
        data = response.json()

        assert data["strict_managed_mode"] is True
        assert data["architecture_followed"] is False
        assert len(data["gaps"]) > 0

    def test_production_mode_reports_followed_when_configured(self, monkeypatch):
        monkeypatch.setattr(auth_mod, "get_current_user", _fake_user)
        monkeypatch.setattr(rbac_mod, "verify_patient_access", _allow_access)
        _set_common_env(monkeypatch, environment="production", postgres=True)
        monkeypatch.setenv("AZURE_BLOB_CONNECTION_STRING", "DefaultEndpointsProtocol=https;AccountName=x;AccountKey=y;EndpointSuffix=core.windows.net")
        monkeypatch.setenv("AZURE_DI_ENDPOINT", "https://example.cognitiveservices.azure.com")
        monkeypatch.setenv("AZURE_DI_KEY", "fake-key")
        monkeypatch.setenv("AZURE_LANGUAGE_ENDPOINT", "https://example-language.cognitiveservices.azure.com")
        monkeypatch.setenv("AZURE_LANGUAGE_KEY", "fake-key")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example-openai.openai.azure.com")
        monkeypatch.setenv("AZURE_OPENAI_KEY", "fake-key")
        monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://example-search.search.windows.net")
        monkeypatch.setenv("AZURE_SEARCH_KEY", "fake-key")
        monkeypatch.setenv("AZURE_TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com")
        monkeypatch.setenv("AZURE_TRANSLATOR_KEY", "fake-key")
        config_mod._settings = None

        response = client.get("/api/system/architecture/compliance")
        assert response.status_code == 200
        data = response.json()

        assert data["strict_managed_mode"] is True
        assert data["architecture_followed"] is True
        assert data["degraded_mode"] is False
        assert data["gaps"] == []
