# tests/functional/test_api_summary.py
# V4 FIXES:
#   NEW-1: Summary is GET + StreamingResponse(PDF)
#   V4-3: Fixed R4-1 which still had a conditional guard.
#         MVP summary.py contract:
#           - patient has nodes -> StreamingResponse(PDF), HTTP 200,
#                                 content-type: application/pdf
#           - patient has 0 nodes -> HTTP 200 + JSON {"error": "..."} (not PDF!)
#             Route uses: if total_nodes == 0: return {"error": "..."}

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _auth(user_id="ramesh-id", tier="free"):
    return patch("api.middleware.auth.get_current_user",
                 return_value={"id": user_id, "tier": tier})


class TestSummaryGeneration:

    def test_generate_summary_returns_pdf(self):
        """
        GET /api/summary/generate -> StreamingResponse(PDF).
        Mocks phig_builder to return a patient with nodes.
        """
        with _auth(), \
             patch("api.routes.summary.phig_builder") as mock_phig, \
             patch("api.routes.summary.generate_health_summary_pdf") as mock_gen, \
             patch("api.routes.summary.blob_service"):
            mock_phig.get_full_patient_graph = \
                __import__("unittest.mock", fromlist=["AsyncMock"]).AsyncMock(
                    return_value={"summary": {"total_nodes": 5}}
                )
            mock_gen.return_value = b"%PDF-1.4 fake pdf content"
            response = client.get("/api/summary/generate")  # GET not POST
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("application/pdf")
            assert response.content[:4] == b"%PDF", \
                "Response body must start with PDF magic bytes"

    def test_summary_has_content_disposition_header(self):
        """PDF response must include content-disposition with filename."""
        with _auth(), \
             patch("api.routes.summary.phig_builder") as mock_phig, \
             patch("api.routes.summary.generate_health_summary_pdf") as mock_gen, \
             patch("api.routes.summary.blob_service"):
            from unittest.mock import AsyncMock
            mock_phig.get_full_patient_graph = AsyncMock(
                return_value={"summary": {"total_nodes": 3}}
            )
            mock_gen.return_value = b"%PDF-1.4 fake"
            response = client.get("/api/summary/generate")
            assert response.status_code == 200
            cd = response.headers.get("content-disposition", "")
            assert "CareOrbit_Summary_" in cd or "attachment" in cd, \
                f"content-disposition missing or incorrect: '{cd}'"

    def test_summary_no_data_returns_json_error(self):
        """
        V4 FIX V4-3: MVP summary.py uses:
            if graph["summary"]["total_nodes"] == 0:
                return {"error": "No health data available..."}
        This returns HTTP 200 with application/json (FastAPI wraps dict as JSON).
        Not a PDF, not a 404. Unconditional assertions — no conditional guards.
        """
        with _auth(user_id="empty-patient-id"), \
             patch("api.routes.summary.phig_builder") as mock_phig, \
             patch("api.routes.summary.verify_patient_access"):
            from unittest.mock import AsyncMock
            mock_phig.get_full_patient_graph = AsyncMock(
                return_value={"summary": {"total_nodes": 0}}
            )
            response = client.get("/api/summary/generate")
            # MVP contract: 200 with JSON error when no nodes exist
            assert response.status_code == 200
            assert "application/json" in response.headers.get("content-type", ""), \
                "Empty patient must return JSON (not PDF)"
            data = response.json()
            assert "error" in data, \
                f"JSON response must contain 'error' field, got: {data}"

    def test_summary_requires_auth(self):
        """No auth -> 401 or 403."""
        response = client.get("/api/summary/generate")
        assert response.status_code in (401, 403)

    def test_summary_caregiver_view_access(self):
        """Caregiver with 'view' permission can generate summary for patient."""
        with patch("api.middleware.auth.get_current_user",
                   return_value={"id": "caregiver-id", "tier": "free"}), \
             patch("api.routes.summary.verify_patient_access",
                   return_value={"access_type": "caregiver", "permission_level": "view"}), \
             patch("api.routes.summary.phig_builder") as mock_phig, \
             patch("api.routes.summary.generate_health_summary_pdf") as mock_gen, \
             patch("api.routes.summary.blob_service"):
            from unittest.mock import AsyncMock
            mock_phig.get_full_patient_graph = AsyncMock(
                return_value={"summary": {"total_nodes": 4}}
            )
            mock_gen.return_value = b"%PDF-1.4 caregiver summary"
            response = client.get("/api/summary/generate?patient_id=patient-123")
            assert response.status_code == 200
