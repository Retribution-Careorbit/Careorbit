import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.mark.deployment
class TestSecurityHeaders:

    def test_hsts_header_present(self):
        response = client.get("/health")
        hsts = response.headers.get("Strict-Transport-Security")
        assert hsts is not None, "Missing Strict-Transport-Security header"
        assert "max-age=" in hsts
        max_age = int(hsts.split("max-age=")[1].split(";")[0].strip())
        assert max_age >= 31536000, \
            f"HSTS max-age must be >= 31536000 (1 year), got {max_age}"

    def test_content_type_options_header(self):
        response = client.get("/health")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_frame_options_header(self):
        response = client.get("/health")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_referrer_policy_header(self):
        response = client.get("/health")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_security_headers_on_api_endpoint(self):
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrong"
        })
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_security_headers_on_404(self):
        response = client.get("/nonexistent-path-xyz")
        if response.status_code == 404:
            assert response.headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.deployment
class TestCORSProduction:

    def test_cors_no_wildcard_in_production(self):
        import os
        if os.environ.get("ENVIRONMENT") == "production":
            response = client.options("/health", headers={
                "Origin": "https://evil.com",
                "Access-Control-Request-Method": "GET",
            })
            allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
            assert allow_origin != "*", \
                "Production must not use wildcard CORS"

    def test_cors_allows_static_web_app_origin(self):
        import os
        if os.environ.get("ENVIRONMENT") == "production":
            response = client.options("/health", headers={
                "Origin": "https://careorbit-web-prod.azurestaticapps.net",
                "Access-Control-Request-Method": "GET",
            })
            allow_origin = response.headers.get("Access-Control-Allow-Origin", "")
            assert "azurestaticapps" in allow_origin or allow_origin == ""


@pytest.mark.deployment
class TestDPDPCompliance:

    def test_delete_account_endpoint_exists(self):
        response = client.delete("/api/auth/delete-account", headers={
            "Authorization": "Bearer invalid-token"
        })
        assert response.status_code in (401, 403, 200, 422), \
            "DELETE /api/auth/delete-account must exist (got 404)"

    def test_export_data_endpoint_exists(self):
        response = client.get("/api/auth/export-data", headers={
            "Authorization": "Bearer invalid-token"
        })
        assert response.status_code in (401, 403, 200, 422), \
            "GET /api/auth/export-data must exist (got 404)"

    def test_delete_account_requires_auth(self):
        response = client.delete("/api/auth/delete-account")
        assert response.status_code in (401, 403, 422), \
            "delete-account must require authentication"

    def test_export_data_requires_auth(self):
        response = client.get("/api/auth/export-data")
        assert response.status_code in (401, 403, 422), \
            "export-data must require authentication"
