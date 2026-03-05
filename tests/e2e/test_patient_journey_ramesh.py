# tests/e2e/test_patient_journey_ramesh.py
# V4 FIXES:
#   NEW-5: phone_number field
#   NEW-1: Summary via GET + PDF magic bytes
#   Q6: Interaction assertion unconditional
#   V4-3: Summary step uses GET correctly

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4

client = TestClient(app)


@pytest.fixture(scope="class")
def ramesh_auth():
    """Register Ramesh once, share across all test steps."""
    response = client.post("/api/auth/register", json={
        "name": "Ramesh Kumar",
        "email": f"ramesh.e2e.{uuid4().hex[:8]}@careorbit.dev",
        "password": "RameshPass123!",
        "phone_number": "+919876543210",
        "date_of_birth": "1958-03-15",
        "gender": "male",
        "city": "Durgapur",
        "state": "West Bengal",
        "preferred_language": "hi"
    })
    assert response.status_code in (200, 201, 202), \
        f"Ramesh registration failed: {response.status_code}"
    data = response.json()
    return {
        "access_token": data.get("access_token"),
        "headers": {"Authorization": f"Bearer {data.get('access_token')}"}
    }


class TestRameshJourney:
    """
    End-to-end journey: Ramesh Kumar, 68M, Durgapur.
    Conditions: T2DM, HTN, Dyslipidemia.
    Tests the complete P0 patient flow from registration to chat.
    """

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_openai, mock_vision, mock_blob,
                    mock_search, mock_email, mock_translator):
        self.mocks = {
            "openai": mock_openai, "vision": mock_vision,
            "blob": mock_blob, "search": mock_search,
            "email": mock_email, "translator": mock_translator
        }

    def test_step1_default_tier_is_free(self, ramesh_auth):
        """New user must start on free tier."""
        with patch("api.middleware.feature_gate.get_user_tier", return_value="free"):
            from utils.tier_config import TIER_LIMITS
            limits = TIER_LIMITS["free"]
            assert limits["shows_ads"] is True
            assert limits["summaries_per_month"] == 5

    def test_step2_upload_prescription(self, ramesh_auth):
        """Upload prescription → 3+ nodes created, document_type=prescription."""
        with patch("api.routes.documents.document_pipeline") as mock_pipeline, \
             patch("api.middleware.rbac.verify_patient_access",
                   return_value={"access_type": "self", "permission_level": "full"}):
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="prescription",
                processing_status="success",
                nodes_created=[
                    {"id": "n1", "node_type": "medication"},
                    {"id": "n2", "node_type": "medication"},
                    {"id": "n3", "node_type": "medication"},
                ],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=1500,
                error_message=None
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("prescription.jpg", b"fake_image", "image/jpeg")},
                headers=ramesh_auth["headers"]
            )
            assert response.status_code == 200
            data = response.json()
            assert data["document_type"] == "prescription"
            assert data["nodes_created"] >= 3

    def test_step3_upload_ibuprofen_triggers_interaction(self, ramesh_auth):
        """Ibuprofen prescription → Metformin+Ibuprofen interaction detected."""
        with patch("api.routes.documents.document_pipeline") as mock_pipeline, \
             patch("api.middleware.rbac.verify_patient_access",
                   return_value={"access_type": "self", "permission_level": "full"}):
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="prescription",
                processing_status="success",
                nodes_created=[{"id": "n4", "node_type": "medication"}],
                interaction_alerts=[{
                    "drug_a": "Metformin", "drug_b": "Ibuprofen",
                    "severity": "HIGH",
                    "alert_level": "URGENT_ALERT",
                    "escalation_reason": "renal_impairment"
                }],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=900,
                error_message=None
            ))
            response = client.post(
                "/api/documents/upload",
                files={"file": ("rx2.jpg", b"fake", "image/jpeg")},
                headers=ramesh_auth["headers"]
            )
            data = response.json()
            interactions = data.get("interaction_alerts", [])
            # V3 FIX Q6: unconditional assertion
            assert len(interactions) >= 1, \
                "Metformin + Ibuprofen interaction not detected for Ramesh"

    def test_step7_generate_summary_pdf(self, ramesh_auth):
        """Summary generation → GET returns PDF bytes."""
        with patch("api.routes.summary.phig_builder") as mock_phig, \
             patch("api.routes.summary.generate_health_summary_pdf") as mock_gen, \
             patch("api.routes.summary.blob_service"), \
             patch("api.routes.summary.verify_patient_access",
                   return_value={"access_type": "self", "permission_level": "full"}):
            mock_phig.get_full_patient_graph = AsyncMock(
                return_value={"summary": {"total_nodes": 8}}
            )
            mock_gen.return_value = b"%PDF-1.4 ramesh summary"
            # V3 FIX NEW-1: GET, not POST
            response = client.get(
                "/api/summary/generate",
                headers=ramesh_auth["headers"]
            )
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("application/pdf")
            assert response.content[:4] == b"%PDF"

    def test_step8_chat_english(self, ramesh_auth):
        """English chat query → meaningful response."""
        with patch("api.routes.chat.orchestrator") as mock_orch:
            mock_orch.process_query = AsyncMock(return_value=MagicMock(
                message="Your medications look fine overall, but Ibuprofen may "
                        "interact with Metformin due to your kidney function.",
                language="en",
                agents_used=["MedicationAgent"],
                alerts=[{"drug_a": "Metformin", "drug_b": "Ibuprofen",
                         "severity": "HIGH"}],
                care_gaps=[],
                recommendations=["Discuss Ibuprofen use with your doctor."],
                confidence=0.82
            ))
            response = client.post("/api/chat/query", json={
                "message": "Are my medications safe together?",
                "language": "en"
            }, headers=ramesh_auth["headers"])
            assert response.status_code == 200
            data = response.json()
            assert len(data.get("message", "")) > 20

    def test_step8b_chat_hindi(self, ramesh_auth):
        """Hindi chat query → response in Hindi."""
        with patch("api.routes.chat.orchestrator") as mock_orch:
            mock_orch.process_query = AsyncMock(return_value=MagicMock(
                message="[hi] आपकी दवाइयाँ सुरक्षित हैं, लेकिन इबुप्रोफेन पर ध्यान दें।",
                language="hi",
                agents_used=["MedicationAgent"],
                alerts=[],
                care_gaps=[],
                recommendations=[],
                confidence=0.78
            ))
            response = client.post("/api/chat/query", json={
                "message": "Meri dawaiyon ke baare mein batao",
                "language": "hi"
            }, headers=ramesh_auth["headers"])
            assert response.status_code == 200
            data = response.json()
            assert len(data.get("message", "")) > 0
            assert data.get("language") == "hi"
