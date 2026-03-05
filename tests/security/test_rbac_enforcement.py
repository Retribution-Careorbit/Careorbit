# tests/security/test_rbac_enforcement.py

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestRBACEnforcement:

    def test_unauthenticated_request_rejected(self):
        """All protected endpoints reject requests without Bearer token."""
        endpoints = [
            ("GET", "/api/patients/overview"),
            ("GET", "/api/patients/medications"),
            ("POST", "/api/documents/upload"),
            ("GET", "/api/summary/generate"),
        ]
        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path)
            assert response.status_code in (401, 403), \
                f"{method} {path} returned {response.status_code} without auth"

    def test_invalid_jwt_rejected(self):
        """Tampered or invalid JWT returns 401."""
        response = client.get(
            "/api/patients/overview",
            headers={"Authorization": "Bearer invalid.jwt.token"}
        )
        assert response.status_code == 401

    def test_caregiver_cannot_access_unlinked_patient(self):
        """Caregiver without a caregiver_link to a patient gets 403."""
        with patch("api.middleware.auth.get_current_user",
                   return_value={"id": "caregiver-no-link", "tier": "free"}), \
             patch("api.middleware.rbac.async_session") as mock_session:
            session = __import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock()
            session.__aenter__ = session.__aexit__ = session
            # No caregiver link found
            session.execute = __import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock(
                return_value=__import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(
                    mappings=lambda: __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock(
                        first=lambda: None  # No link
                    )
                )
            )
            mock_session.return_value = session

            response = client.get("/api/patients/medications?patient_id=another-patient")
            assert response.status_code == 403
