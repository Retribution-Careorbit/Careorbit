# tests/functional/test_api_documents_boundaries.py
# ADD-3: Boundary tests for upload endpoint.
# Tests: file too large, wrong MIME type, zero-byte file.
# MVP documents.py enforces: allowed_types, 10MB limit.

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def _auth():
    return patch("api.middleware.auth.get_current_user",
                 return_value={"id": "patient-id", "tier": "free"})


def _rbac_allow():
    return patch("api.middleware.rbac.verify_patient_access",
                 return_value={"access_type": "self", "permission_level": "full"})


class TestUploadFileBoundaries:

    def test_file_too_large_rejected(self):
        """
        MVP documents.py: if file.size > 10 * 1024 * 1024 -> HTTP 400.
        10MB + 1 byte should be rejected.
        """
        large_file = b"X" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte
        with _auth(), _rbac_allow():
            response = client.post(
                "/api/documents/upload",
                files={"file": ("large.jpg", large_file, "image/jpeg")}
            )
            assert response.status_code == 400, \
                "Files > 10MB must be rejected with HTTP 400"

    def test_pdf_content_type_rejected(self):
        """
        MVP allowed_types: ['image/jpeg', 'image/png', 'image/webp', 'image/heic'].
        PDF is NOT in the allowed list.
        """
        with _auth(), _rbac_allow():
            response = client.post(
                "/api/documents/upload",
                files={"file": ("report.pdf", b"fake_pdf_data", "application/pdf")}
            )
            assert response.status_code == 400, \
                "PDF uploads must be rejected (image-only in Phase 1)"

    def test_text_file_content_type_rejected(self):
        with _auth(), _rbac_allow():
            response = client.post(
                "/api/documents/upload",
                files={"file": ("notes.txt", b"some text", "text/plain")}
            )
            assert response.status_code == 400

    def test_jpeg_within_limit_accepted(self):
        """1KB JPEG — should pass content-type and size checks."""
        with _auth(), _rbac_allow(), \
             patch("api.routes.documents.document_pipeline") as mock_pipeline:
            from unittest.mock import AsyncMock, MagicMock
            from uuid import uuid4
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()), document_type="prescription",
                processing_status="success", nodes_created=[],
                interaction_alerts=[], care_gap_alerts=[],
                confirmation_needed=[], processing_time_ms=500,
                error_message=None
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("rx.jpg", b"X" * 1024, "image/jpeg")}
            )
            assert response.status_code != 400

    def test_png_accepted(self):
        with _auth(), _rbac_allow(), \
             patch("api.routes.documents.document_pipeline") as mock_pipeline:
            from unittest.mock import AsyncMock, MagicMock
            from uuid import uuid4
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()), document_type="lab_report",
                processing_status="success", nodes_created=[],
                interaction_alerts=[], care_gap_alerts=[],
                confirmation_needed=[], processing_time_ms=500,
                error_message=None
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("lab.png", b"PNG_fake", "image/png")}
            )
            assert response.status_code != 400

    def test_missing_file_field_rejected(self):
        """POST without the 'file' field -> 422 Unprocessable Entity."""
        with _auth(), _rbac_allow():
            response = client.post("/api/documents/upload", json={"no_file": "here"})
            assert response.status_code == 422
