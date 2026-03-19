# tests/functional/test_api_documents.py

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

from db.runtime_store import get_runtime_appointments
from db.runtime_store import get_extracted_medications
from api.routes.reminders import _reminders_store

client = TestClient(app)


def _auth(user_id="patient-id", tier="free"):
    return patch("api.middleware.auth.get_current_user",
                 return_value={"id": user_id, "tier": tier})


def _rbac_allow():
    return patch("api.middleware.rbac.verify_patient_access",
                 return_value={"access_type": "self", "permission_level": "full"})


class TestDocumentUpload:

    def test_needs_confirmation_upload_does_not_auto_add_medications(self):
        test_patient = f"patient-{uuid4().hex[:8]}"
        with _auth(user_id=test_patient), _rbac_allow(), \
             patch("api.routes.documents.document_pipeline") as mock_pipeline, \
             patch("api.routes.documents.persist_document_graph", new=AsyncMock(return_value={"status": "ok"})):
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="prescription",
                processing_status="needs_confirmation",
                nodes_created=[{"id": "n1", "node_type": "medication"}],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[{"id": "n1", "node_type": "medication"}],
                processing_time_ms=900,
                error_message=None,
                extracted_data={
                    "medications": [{"name": "Metformin", "dosage": "500 mg", "frequency": ""}],
                    "labs": [],
                    "conditions": [],
                    "summary": "Low confidence extraction",
                    "context": {},
                    "quality": {"source_type": "prescription_digital", "ocr_confidence": 0.48},
                },
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("unclear.pdf", b"fake", "application/pdf")}
            )

        assert response.status_code == 200
        assert response.json()["status"] == "needs_confirmation"
        meds_after = get_extracted_medications(test_patient)
        assert all(str(m.get("name", "")).lower() != "metformin" for m in meds_after)

    def test_upload_auto_updates_appointments_and_reminders(self):
        test_patient = f"patient-{uuid4().hex[:8]}"
        with _auth(user_id=test_patient), _rbac_allow(), \
             patch("api.routes.documents.document_pipeline") as mock_pipeline, \
             patch("api.routes.documents.persist_document_graph", new=AsyncMock(return_value={"status": "ok"})):
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="prescription",
                processing_status="success",
                nodes_created=[{"id": "n1", "node_type": "medication"}],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=1200,
                error_message=None,
                extracted_data={
                    "summary": "Parsed prescription",
                    "medications": [
                        {
                            "name": "Metformin",
                            "dosage": "500 mg",
                            "frequency": "twice daily",
                        }
                    ],
                    "labs": [],
                    "conditions": [],
                    "context": {
                        "doctor_name": "Dr. Rao",
                        "doctor_specialty": "General Physician",
                        "prescribed_on": "2026-03-10",
                        "follow_up_date": "2026-03-24",
                        "is_ongoing": True,
                    },
                    "quality": {
                        "source_type": "prescription_digital",
                        "ocr_confidence": 0.88,
                    },
                },
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("prescription.pdf", b"fake_pdf", "application/pdf")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data.get("appointments_created") == 2
        assert data.get("reminders_created", 0) >= 1

        runtime_appointments = get_runtime_appointments(test_patient)
        assert any(a.get("source_marker", "").startswith("doc-visit-") for a in runtime_appointments)
        assert any(a.get("source_marker", "").startswith("doc-followup-") for a in runtime_appointments)

        patient_reminders = [r for r in _reminders_store.values() if r.get("user_id") == test_patient]
        assert len(patient_reminders) >= 1
        assert any((r.get("source_marker") or "").startswith("doc-reminder:") for r in patient_reminders)

    def test_upload_promotes_unknown_type_to_lab_report_when_markers_present(self):
        with _auth(), _rbac_allow(), \
             patch("api.routes.documents.document_pipeline") as mock_pipeline, \
             patch("api.routes.documents.persist_document_graph", new=AsyncMock(return_value={"status": "ok"})):
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="medical_document",
                processing_status="success",
                nodes_created=[{"id": "lab1", "node_type": "lab_value"}],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=900,
                error_message=None,
                extracted_data={
                    "summary": "Lab values extracted",
                    "medications": [],
                    "conditions": [],
                    "labs": [{"name": "HbA1c", "value": 8.2, "unit": "%"}],
                    "context": {},
                    "quality": {
                        "source_type": "lab_report_digital",
                        "ocr_confidence": 0.84,
                    },
                },
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("report.pdf", b"fake_pdf", "application/pdf")}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["document_type"] == "lab_report"

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
