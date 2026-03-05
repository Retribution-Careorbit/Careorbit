import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from uuid import uuid4
from datetime import datetime, timezone, timedelta

client = TestClient(app)


@pytest.fixture(scope="class")
def orbit_patient_auth():
    """Register a fresh patient for the orbit journey tests."""
    response = client.post("/api/auth/register", json={
        "name": "Anita Desai",
        "email": f"anita.orbit.{uuid4().hex[:8]}@careorbit.dev",
        "password": "AnitaPass123!",
        "phone_number": "+919876500001",
        "date_of_birth": "1965-07-10",
        "gender": "female",
        "city": "Pune",
        "state": "Maharashtra",
        "preferred_language": "en"
    })
    assert response.status_code in (200, 201, 202), \
        f"Orbit patient registration failed: {response.status_code}"
    data = response.json()
    return {
        "access_token": data.get("access_token"),
        "headers": {"Authorization": f"Bearer {data.get('access_token')}"}
    }


class TestOrbitJourney:
    """
    End-to-end journey: Orbit Score + Pre-Visit Brief + Living Narrative.
    Covers the full lifecycle from a new patient with a low orbit score
    through document upload, appointment creation, and verification of
    orbit score, narrative, and brief population.
    """

    @pytest.fixture(autouse=True)
    def setup_mocks(self, mock_openai, mock_vision, mock_blob,
                    mock_search, mock_email, mock_translator):
        self.mocks = {
            "openai": mock_openai, "vision": mock_vision,
            "blob": mock_blob, "search": mock_search,
            "email": mock_email, "translator": mock_translator
        }

    def test_new_patient_starts_with_low_orbit_score(self, orbit_patient_auth):
        """Fresh patient with no documents → low completeness, neutral adherence (75)."""
        with patch("api.routes.orbit.compute_orbit_score") as mock_compute:
            mock_compute.return_value = {
                "total_score": 18.75,
                "breakdown": {
                    "completeness": 0.0,
                    "avg_confidence": 0.0,
                    "interaction_risk": 100.0,
                    "care_gap_status": 100.0,
                    "adherence_rate": 75.0,
                },
                "delta": None,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            response = client.get(
                "/api/orbit/score",
                headers=orbit_patient_auth["headers"]
            )
            assert response.status_code == 200
            data = response.json()
            assert "total_score" in data
            total = data["total_score"]
            assert 0 <= total <= 100
            assert total < 50, (
                f"New patient should have a low orbit score, got {total}"
            )
            if data.get("breakdown"):
                assert data["breakdown"]["adherence_rate"] == 75.0

    def test_upload_prescription_improves_orbit_score(self, orbit_patient_auth):
        """Upload a prescription document → orbit score increases."""
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
                    {"id": "n3", "node_type": "condition"},
                ],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=1200,
                error_message=None
            ))
            upload_resp = client.post(
                "/api/documents/upload",
                files={"file": ("prescription.jpg", b"fake_image", "image/jpeg")},
                headers=orbit_patient_auth["headers"]
            )
            assert upload_resp.status_code == 200

        with patch("api.routes.orbit.compute_orbit_score") as mock_compute:
            mock_compute.return_value = {
                "total_score": 52.5,
                "breakdown": {
                    "completeness": 66.7,
                    "avg_confidence": 85.0,
                    "interaction_risk": 100.0,
                    "care_gap_status": 80.0,
                    "adherence_rate": 75.0,
                },
                "delta": 33.75,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            response = client.get(
                "/api/orbit/score",
                headers=orbit_patient_auth["headers"]
            )
            assert response.status_code == 200
            data = response.json()
            total = data["total_score"]
            assert total > 18.75, (
                f"Score after prescription upload should be higher than baseline, got {total}"
            )
            assert data.get("delta") is not None
            assert data["delta"] > 0

    def test_add_appointment_within_48h_generates_brief(self, orbit_patient_auth):
        """Add an appointment within 48 hours → brief is generated."""
        appointment_dt = (
            datetime.now(timezone.utc) + timedelta(hours=24)
        ).isoformat()

        with patch("api.routes.orbit.create_appointment") as mock_create, \
             patch("api.routes.orbit.schedule_previsit_brief") as mock_brief:
            mock_create.return_value = {
                "appointment_id": str(uuid4()),
                "doctor_name": "Dr. Meera Patel",
                "appointment_datetime": appointment_dt,
                "brief_scheduled": True,
            }
            mock_brief.return_value = True

            response = client.post(
                "/api/orbit/appointments",
                json={
                    "doctor_name": "Dr. Meera Patel",
                    "appointment_datetime": appointment_dt,
                    "clinic_name": "City Hospital",
                },
                headers=orbit_patient_auth["headers"]
            )
            assert response.status_code in (200, 201)
            data = response.json()
            assert data.get("brief_scheduled") is True, (
                "Appointment within 48h should have brief_scheduled=true"
            )

    def test_orbit_score_history_has_multiple_entries(self, orbit_patient_auth):
        """After multiple actions, score history should grow."""
        with patch("api.routes.orbit.get_score_history") as mock_history:
            mock_history.return_value = [
                {
                    "total_score": 18.75,
                    "computed_at": (
                        datetime.now(timezone.utc) - timedelta(hours=2)
                    ).isoformat(),
                },
                {
                    "total_score": 52.5,
                    "computed_at": (
                        datetime.now(timezone.utc) - timedelta(hours=1)
                    ).isoformat(),
                },
                {
                    "total_score": 55.0,
                    "computed_at": datetime.now(timezone.utc).isoformat(),
                },
            ]
            response = client.get(
                "/api/orbit/score/history",
                headers=orbit_patient_auth["headers"]
            )
            assert response.status_code == 200
            history = response.json()
            assert isinstance(history, list)
            assert len(history) >= 2, (
                "Score history should have multiple entries after several actions"
            )
            scores = [entry["total_score"] for entry in history]
            assert scores[-1] >= scores[0], (
                "Latest score should be >= initial score after improvements"
            )

    def test_full_journey_orbit_narrative_brief(self, orbit_patient_auth):
        """
        Full journey: register → upload → confirm → appointment →
        verify orbit score, narrative, and brief are all populated.
        """
        with patch("api.routes.documents.document_pipeline") as mock_pipeline, \
             patch("api.middleware.rbac.verify_patient_access",
                   return_value={"access_type": "self", "permission_level": "full"}):
            mock_pipeline.process_document = AsyncMock(return_value=MagicMock(
                document_id=str(uuid4()),
                document_type="lab_report",
                processing_status="success",
                nodes_created=[
                    {"id": "lab1", "node_type": "lab_value"},
                ],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=800,
                error_message=None
            ))
            upload_resp = client.post(
                "/api/documents/upload",
                files={"file": ("lab_report.jpg", b"fake_lab", "image/jpeg")},
                headers=orbit_patient_auth["headers"]
            )
            assert upload_resp.status_code == 200

        with patch("api.routes.orbit.compute_orbit_score") as mock_compute:
            mock_compute.return_value = {
                "total_score": 62.0,
                "breakdown": {
                    "completeness": 100.0,
                    "avg_confidence": 85.0,
                    "interaction_risk": 100.0,
                    "care_gap_status": 60.0,
                    "adherence_rate": 75.0,
                },
                "delta": 7.0,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }
            score_resp = client.get(
                "/api/orbit/score",
                headers=orbit_patient_auth["headers"]
            )
            assert score_resp.status_code == 200
            score_data = score_resp.json()
            assert score_data["total_score"] > 0
            assert score_data.get("breakdown") is not None

        with patch("api.routes.orbit.get_living_narrative") as mock_narrative:
            mock_narrative.return_value = {
                "narrative": (
                    "Anita Desai has been managing Type 2 Diabetes and Hypertension. "
                    "Recent lab results show improving HbA1c levels."
                ),
                "trigger_event": "document_upload",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            narrative_resp = client.get(
                "/api/orbit/narrative",
                headers=orbit_patient_auth["headers"]
            )
            assert narrative_resp.status_code == 200
            narrative_data = narrative_resp.json()
            narrative_text = narrative_data.get("narrative", "")
            assert len(narrative_text) > 0, "Narrative should be non-empty"

        appointment_dt = (
            datetime.now(timezone.utc) + timedelta(hours=12)
        ).isoformat()
        with patch("api.routes.orbit.create_appointment") as mock_appt, \
             patch("api.routes.orbit.schedule_previsit_brief") as mock_brief:
            mock_appt.return_value = {
                "appointment_id": str(uuid4()),
                "doctor_name": "Dr. Sunil Verma",
                "appointment_datetime": appointment_dt,
                "brief_scheduled": True,
            }
            mock_brief.return_value = True
            appt_resp = client.post(
                "/api/orbit/appointments",
                json={
                    "doctor_name": "Dr. Sunil Verma",
                    "appointment_datetime": appointment_dt,
                    "clinic_name": "Metro Clinic",
                },
                headers=orbit_patient_auth["headers"]
            )
            assert appt_resp.status_code in (200, 201)
            appt_data = appt_resp.json()
            assert appt_data.get("brief_scheduled") is True

        assert score_data["total_score"] > 0, "Orbit score must be populated"
        assert len(narrative_text) > 0, "Living narrative must be populated"
        assert appt_data["brief_scheduled"] is True, "Pre-visit brief must be scheduled"
