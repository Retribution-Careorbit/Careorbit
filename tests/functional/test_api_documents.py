# tests/functional/test_api_documents.py

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4
import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.runtime_store import save_pending_document_review
from graph.confidence import ConfidenceCalculator

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

    def test_upload_lab_report_returns_lab_persistence_metadata(self):
        with _auth(), _rbac_allow(), \
             patch("api.routes.documents.document_pipeline") as mock_pipeline, \
             patch("api.routes.documents._persist_labs_to_phig_db", AsyncMock(return_value=(True, 2, []))):
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="lab_report",
                processing_status="success",
                nodes_created=[{"id": "n-l1", "node_type": "lab_value"}],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=900,
                error_message=None,
                extracted_data={
                    "doctor_name": "",
                    "medications": [],
                    "labs": [
                        {"name": "Creatinine", "value": 1.2, "unit": "mg/dL", "loinc": "2160-0"},
                        {"name": "eGFR", "value": 72, "unit": "mL/min", "loinc": "33914-3"},
                    ],
                    "missing_fields": [],
                    "lab_rejections": [],
                    "clinical_entities": [],
                },
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("lab_report.jpg", b"fake_lab_data", "image/jpeg")}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["document_type"] == "lab_report"
            assert data["lab_persistence"] == "database"
            assert data["labs_added"] == 2
            assert data["lab_rejections"] == []


class TestPostConfirmationPipeline:

    def test_confirm_runs_pipeline_and_returns_trace(self):
        async def fake_user(_request):
            return {"id": "patient-id", "tier": "free"}

        async def fake_access(*_args, **_kwargs):
            return True

        save_pending_document_review(
            "patient-id",
            "doc-pipeline-1",
            {
                "doctor_name": "Dr. Rao",
                "medications": [{"name": "Metformin", "dosage": "500 mg", "frequency": "BD", "dose_to_take": "1 tablet"}],
                "missing_fields": [],
                "document_type": "prescription",
            },
        )

        with (
            patch.object(auth_mod, "get_current_user", fake_user),
            patch.object(rbac_mod, "verify_patient_access", fake_access),
            patch("api.routes.documents.language_service.recognize_health_entities", AsyncMock(return_value=[])),
            patch("api.routes.documents.openai_service.chat", AsyncMock(return_value='{"doctor_name":"Dr. Rao","medications":[{"name":"Metformin","dosage":"500 mg","frequency":"BD","dose_to_take":"1 tablet","validation_status":"confirmed","validation_notes":"ok"}],"validation_summary":"ok"}')),
            patch("api.routes.documents.phig_builder.check_interactions_for_node", AsyncMock(return_value=[])),
        ):

            response = client.post(
                "/api/documents/confirm/doc-pipeline-1",
                json={
                    "doctor_name": "Dr. Rao",
                    "medications": [
                        {
                            "name": "Metformin",
                            "dosage": "500 mg",
                            "frequency": "BD",
                            "dose_to_take": "1 tablet",
                        }
                    ],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "confirmed"
        assert data["pipeline_trace"]["language_ner"] in {"ok", "fallback"}
        assert data["pipeline_trace"]["validation"] == "ok"
        assert data["pipeline_trace"]["phig_write"] in {"ok", "fallback"}
        assert data["medications_added"] >= 1

    def test_confirm_applies_deterministic_confidence_formula(self):
        async def fake_user(_request):
            return {"id": "patient-id", "tier": "free"}

        async def fake_access(*_args, **_kwargs):
            return True

        save_pending_document_review(
            "patient-id",
            "doc-pipeline-confidence-1",
            {
                "doctor_name": "Dr. Rao",
                "medications": [{"name": "Metformin", "dosage": "500 mg", "frequency": "BD", "dose_to_take": "1 tablet"}],
                "missing_fields": [],
                "document_type": "prescription",
            },
        )

        expected_confidence = ConfidenceCalculator.calculate_medication_confidence(
            source_type="patient_confirmed",
            ocr_avg_confidence=1.0,
            drug_match_score=1.0,
            dosage_parsed=True,
            date_found=False,
            patient_confirmed=True,
            ner_match=True,
        ).final_score

        with (
            patch.object(auth_mod, "get_current_user", fake_user),
            patch.object(rbac_mod, "verify_patient_access", fake_access),
            patch(
                "api.routes.documents.language_service.recognize_health_entities",
                AsyncMock(return_value=[{"text": "Metformin", "coding": [{"name": "RxNorm", "id": "6809"}]}]),
            ),
            patch("api.routes.documents.openai_service.chat", AsyncMock(return_value='{"doctor_name":"Dr. Rao","medications":[{"name":"Metformin","dosage":"500 mg","frequency":"BD","dose_to_take":"1 tablet","validation_status":"confirmed","validation_notes":"ok"}],"validation_summary":"ok"}')),
            patch("api.routes.documents.phig_builder.check_interactions_for_node", AsyncMock(return_value=[])),
        ):

            response = client.post(
                "/api/documents/confirm/doc-pipeline-confidence-1",
                json={
                    "doctor_name": "Dr. Rao",
                    "medications": [
                        {
                            "name": "Metformin",
                            "dosage": "500 mg",
                            "frequency": "BD",
                            "dose_to_take": "1 tablet",
                        }
                    ],
                },
            )

        assert response.status_code == 200
        data = response.json()
        returned_confidence = data["medications"][0]["confidence"]
        assert returned_confidence == expected_confidence

    def test_confirm_rolls_back_when_consistency_fails(self):
        async def fake_user(_request):
            return {"id": "patient-id", "tier": "free"}

        async def fake_access(*_args, **_kwargs):
            return True

        save_pending_document_review(
            "patient-id",
            "doc-pipeline-rollback-1",
            {
                "doctor_name": "Dr. Rao",
                "medications": [{"name": "Metformin", "dosage": "500 mg", "frequency": "BD", "dose_to_take": "1 tablet"}],
                "missing_fields": [],
                "document_type": "prescription",
            },
        )

        with (
            patch.object(auth_mod, "get_current_user", fake_user),
            patch.object(rbac_mod, "verify_patient_access", fake_access),
            patch("api.routes.documents.language_service.recognize_health_entities", AsyncMock(return_value=[])),
            patch("api.routes.documents.openai_service.chat", AsyncMock(return_value='{"doctor_name":"Dr. Rao","medications":[{"name":"Metformin","dosage":"500 mg","frequency":"BD","dose_to_take":"1 tablet","validation_status":"confirmed","validation_notes":"ok"}],"validation_summary":"ok"}')),
            patch("api.routes.documents.phig_builder.check_interactions_for_node", AsyncMock(return_value=[])),
            patch("api.routes.documents.phig_integrity.create_snapshot", AsyncMock(return_value="snapshot-1")),
            patch("api.routes.documents._persist_medications_to_phig_db", AsyncMock(return_value=(True, 1))),
            patch("api.routes.documents.phig_integrity.verify_consistency", AsyncMock(return_value={"passed": False, "errors": ["impossible_lab_value_unit"]})),
            patch("api.routes.documents.phig_integrity.rollback_snapshot", AsyncMock(return_value=True)),
        ):
            response = client.post(
                "/api/documents/confirm/doc-pipeline-rollback-1",
                json={
                    "doctor_name": "Dr. Rao",
                    "medications": [
                        {
                            "name": "Metformin",
                            "dosage": "500 mg",
                            "frequency": "BD",
                            "dose_to_take": "1 tablet",
                        }
                    ],
                },
            )

        assert response.status_code == 500
        data = response.json()
        detail = data["detail"]
        assert detail["error"] == "phig_consistency_failed_after_write"
        assert detail["rollback"] == "applied"
        assert "impossible_lab_value_unit" in detail["consistency_errors"]
        assert detail["pipeline_trace"]["consistency_check"] == "failed"
        assert detail["pipeline_trace"]["rollback"] == "applied"
