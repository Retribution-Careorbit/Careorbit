# tests/functional/test_api_documents.py

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


def _auth(user_id="patient-id", tier="free"):
    return patch("api.middleware.auth.get_current_user",
                 return_value={"id": user_id, "tier": tier})


def _rbac_allow():
    return patch("api.middleware.rbac.verify_patient_access",
                 return_value={"access_type": "self", "permission_level": "full"})


class TestDocumentUpload:

    def test_upload_prescription_success(self):
        with _auth(), _rbac_allow(), \
             patch("api.routes.documents.document_pipeline") as mock_pipeline:
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="prescription",
                processing_status="success",
                nodes_created=[{"id": "n1", "node_type": "medication"},
                               {"id": "n2", "node_type": "medication"}],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=1200,
                error_message=None
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("prescription.jpg", b"fake_image_data", "image/jpeg")}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["document_type"] == "prescription"
            assert data["nodes_created"] >= 2
            assert data["status"] == "success"

    def test_upload_requires_auth(self):
        """No auth header -> 403 (Bearer required)."""
        response = client.post(
            "/api/documents/upload",
            files={"file": ("rx.jpg", b"fake", "image/jpeg")}
        )
        assert response.status_code in (401, 403)

    def test_upload_interaction_detected(self):
        """Ibuprofen + existing Metformin -> interaction alert in response."""
        with _auth(), _rbac_allow(), \
             patch("api.routes.documents.document_pipeline") as mock_pipeline:
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="prescription",
                processing_status="success",
                nodes_created=[{"id": "n3", "node_type": "medication"}],
                interaction_alerts=[{
                    "drug_a": "Metformin", "drug_b": "Ibuprofen",
                    "severity": "Moderate",
                    "description": "NSAIDs may reduce Metformin clearance",
                    "alert_level": "WARNING"
                }],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=980,
                error_message=None
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("rx2.jpg", b"fake", "image/jpeg")}
            )
            assert response.status_code == 200
            data = response.json()
            # V3 FIX Q6: strict assertion, no 'or care_gaps >= 0'
            assert len(data["interaction_alerts"]) >= 1, \
                "Metformin + Ibuprofen interaction not detected"

    def test_upload_returns_needs_confirmation_for_low_confidence(self):
        with _auth(), _rbac_allow(), \
             patch("api.routes.documents.document_pipeline") as mock_pipeline:
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="prescription",
                processing_status="needs_confirmation",
                nodes_created=[{"id": "n4", "node_type": "medication"}],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[{
                    "type": "medication_ambiguous",
                    "node_id": "n4",
                    "original_text": "Glycomet 5OOmg"
                }],
                processing_time_ms=800,
                error_message=None
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("blurry.jpg", b"fake", "image/jpeg")}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "needs_confirmation"
            assert len(data["confirmation_needed"]) >= 1
