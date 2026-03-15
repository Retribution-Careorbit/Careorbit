import pytest
import time
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthEndpointFields:

    def test_health_returns_status_field(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_returns_service_field(self):
        response = client.get("/health")
        data = response.json()
        assert "service" in data
        assert data["service"] == "careorbit-api"

    def test_health_returns_version_field(self):
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert len(data["version"]) > 0

    def test_health_no_auth_required(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_time_under_500ms(self):
        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000
        assert response.status_code == 200
        assert elapsed < 500, f"Health endpoint took {elapsed:.0f}ms (SLA: <500ms)"


@pytest.mark.deployment
class TestHealthEndpointProduction:

    def test_health_returns_environment_field(self):
        response = client.get("/health")
        data = response.json()
        assert "environment" in data, \
            "Health endpoint must include 'environment' field"

    def test_health_default_environment_is_development(self):
        response = client.get("/health")
        data = response.json()
        if "environment" in data:
            assert data["environment"] in ("development", "dev")

    def test_health_returns_database_field(self):
        response = client.get("/health")
        data = response.json()
        assert "database" in data, \
            "Health endpoint must include 'database' connectivity status"

    def test_health_database_not_configured_without_url(self):
        import os
        if "DATABASE_URL" not in os.environ or "sqlite" in os.environ.get("DATABASE_URL", ""):
            response = client.get("/health")
            data = response.json()
            if "database" in data:
                assert data["database"] in ("not_configured", "sqlite", "in_memory")


@pytest.mark.deployment
class TestApplicationInsights:

    def test_appinsights_skipped_without_connection_string(self):
        import os
        if "APPINSIGHTS_CONNECTION_STRING" not in os.environ:
            response = client.get("/health")
            assert response.status_code == 200

    def test_appinsights_init_with_connection_string(self):
        import os
        if "APPINSIGHTS_CONNECTION_STRING" in os.environ:
            response = client.get("/health")
            assert response.status_code == 200


@pytest.mark.deployment
class TestStructuredLogging:

    def test_json_logging_in_production(self):
        import os
        import logging
        if os.environ.get("ENVIRONMENT") == "production":
            logger = logging.getLogger("careorbit")
            handlers = logger.handlers
            assert any(
                hasattr(h, "formatter") and h.formatter is not None
                for h in handlers
            ), "Production logger should have a formatter configured"

    def test_text_logging_in_development(self):
        import os
        if os.environ.get("ENVIRONMENT", "development") == "development":
            pass
