# tests/functional/test_api_health.py
# ADD-5: GET /health readiness probe.
# MVP main.py defines this as the health check endpoint.
# In production CI/CD, used as readiness/liveness probe.

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpoint:

    def test_health_returns_200(self):
        """GET /health must always return 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self):
        """Response body must include status: healthy."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_returns_service_name(self):
        """Response must identify the service."""
        response = client.get("/health")
        data = response.json()
        assert data["service"] == "careorbit-api"

    def test_health_returns_version(self):
        """Response must include a version string."""
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert len(data["version"]) > 0

    def test_health_no_auth_required(self):
        """Health check must not require authentication (used by load balancers)."""
        # Call without any Authorization header
        response = client.get("/health")
        assert response.status_code == 200, \
            "Health endpoint must be accessible without auth"


class TestHealthAuthEndpoint:

    def test_health_auth_returns_200(self):
        response = client.get("/health/auth")
        assert response.status_code == 200

    def test_health_auth_contains_entra_payload(self):
        response = client.get("/health/auth")
        data = response.json()
        assert "status" in data
        assert "provider" in data
        assert data["provider"] == "azure-entra-id"
        assert "entra" in data
        assert "enabled" in data["entra"]
        assert "ready" in data["entra"]
        assert "configured" in data["entra"]
        assert "missing_required" in data["entra"]

    def test_health_auth_does_not_leak_secret_values(self):
        response = client.get("/health/auth")
        data = response.json()
        configured = data["entra"]["configured"]
        for value in configured.values():
            assert isinstance(value, bool)


class TestHealthStartupEndpoint:

    def test_health_startup_returns_200(self):
        response = client.get("/health/startup")
        assert response.status_code == 200

    def test_health_startup_contains_checks(self):
        response = client.get("/health/startup")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("ready", "degraded")
        assert "checks" in data
        assert "database" in data["checks"]
        assert "entra_auth" in data["checks"]
