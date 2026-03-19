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

    def test_health_includes_security_schema_readiness(self):
        """Health payload should include auth/audit schema readiness signal."""
        response = client.get("/health")
        data = response.json()
        assert "security_schema" in data
        assert isinstance(data["security_schema"], dict)
        assert "ready" in data["security_schema"]
        assert "missing" in data["security_schema"]
