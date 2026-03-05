# tests/integration/test_orbit_integration.py
# Integration tests for orbit score computation with document pipeline and PHIG.
# Tests the full flow: document upload → PHIG update → orbit score recompute,
# confirmation → orbit score recompute, appointment brief, and narrative generation.

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def mock_orbit_calculator():
    calculator = MagicMock()
    calculator.compute = MagicMock(return_value={
        "total_score": 72.5,
        "breakdown": {
            "completeness": 80.0,
            "avg_confidence": 85.0,
            "interaction_risk": 60.0,
            "care_gap_status": 70.0,
            "adherence_rate": 75.0,
        },
        "delta": None,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    })
    return calculator


@pytest.fixture
def mock_phig():
    phig = MagicMock()
    phig.get_nodes = MagicMock(return_value=[
        {"type": "medication", "name": "Metformin", "confidence": 0.85},
        {"type": "medication", "name": "Amlodipine", "confidence": 0.82},
        {"type": "condition", "name": "Type 2 Diabetes", "confidence": 0.85},
        {"type": "lab_value", "name": "HbA1c", "value": 7.8, "confidence": 0.93},
    ])
    phig.get_interactions = MagicMock(return_value=[])
    phig.get_care_gaps = MagicMock(return_value=[])
    return phig


@pytest.fixture
def mock_narrative_agent():
    agent = AsyncMock()
    agent.generate_living_narrative = AsyncMock(
        return_value="Ramesh Kumar's health profile was updated after a new prescription was uploaded."
    )
    return agent


@pytest.fixture
def mock_previsit_agent():
    agent = AsyncMock()
    agent.generate_previsit_brief = AsyncMock(return_value={
        "tell_doctor": ["Currently taking Metformin 500mg BD"],
        "ask_doctor": ["Should HbA1c target be revised?"],
        "doctor_may_not_know": ["Also taking Amlodipine prescribed by cardiologist"],
        "bring_to_appointment": ["Health summary PDF", "Recent lab reports"],
        "urgency_flags": [],
    })
    return agent


@pytest.fixture
def pipeline(mock_openai, mock_vision, mock_blob, mock_search, mock_email):
    with patch("pipeline.document_pipeline.openai_service", mock_openai), \
         patch("pipeline.document_pipeline.vision_service", mock_vision), \
         patch("pipeline.document_pipeline.blob_service", mock_blob), \
         patch("pipeline.document_pipeline.search_service", mock_search), \
         patch("pipeline.document_pipeline.email_service", mock_email), \
         patch("pipeline.document_pipeline.db_session", AsyncMock()):
        from pipeline.document_pipeline import DocumentPipeline
        yield DocumentPipeline()


class TestOrbitIntegration:
    """Integration tests for orbit score computation with document pipeline and PHIG."""

    async def test_document_upload_triggers_orbit_recompute(
        self, pipeline, mock_vision, mock_openai, mock_orbit_calculator, mock_db
    ):
        """After document processing, orbit_score_history gets new row."""
        mock_vision.extract_text.return_value = MagicMock(
            full_text="Metformin 500mg BD", lines=["Metformin 500mg BD"],
            avg_confidence=0.94, page_count=1
        )
        mock_vision.classify_document_type.return_value = "prescription"
        mock_openai.extract_structured_data.return_value = {
            "medications": [{"name": "Metformin", "dosage": "500mg", "frequency": "BD"}],
            "doctor_name": "Dr. Roy", "diagnoses": ["DM"], "date": "15/01/2026"
        }

        with patch("graph.orbit_score.OrbitScoreCalculator", return_value=mock_orbit_calculator), \
             patch("pipeline.document_pipeline.OrbitScoreCalculator", return_value=mock_orbit_calculator):
            result = await pipeline.process_document(
                image_bytes=b"fake", patient_id="test-patient",
                uploaded_by="test", file_extension="jpg"
            )

            assert result.processing_status in {"success", "needs_confirmation", "failed"}
            score_result = mock_orbit_calculator.compute.return_value
            assert "total_score" in score_result
            assert 0 <= score_result["total_score"] <= 100

    async def test_confirmation_triggers_orbit_recompute(
        self, mock_orbit_calculator, mock_db
    ):
        """After patient confirms node, orbit score recalculated."""
        mock_db.seed("phig_nodes", [
            {"id": "node-1", "patient_id": "test-patient", "type": "medication",
             "name": "Metformin", "confidence": 0.65, "confirmed": False}
        ])

        confirmed_node = {
            "id": "node-1", "patient_id": "test-patient", "type": "medication",
            "name": "Metformin", "confidence": 0.85, "confirmed": True
        }

        with patch("graph.orbit_score.OrbitScoreCalculator", return_value=mock_orbit_calculator):
            mock_orbit_calculator.compute.return_value = {
                "total_score": 78.0,
                "breakdown": {
                    "completeness": 80.0,
                    "avg_confidence": 90.0,
                    "interaction_risk": 75.0,
                    "care_gap_status": 70.0,
                    "adherence_rate": 75.0,
                },
                "delta": 5.5,
                "computed_at": datetime.now(timezone.utc).isoformat(),
            }

            score = mock_orbit_calculator.compute(
                patient_id="test-patient", trigger="confirmation"
            )
            assert score["total_score"] == 78.0
            assert score["delta"] == 5.5
            mock_orbit_calculator.compute.assert_called_with(
                patient_id="test-patient", trigger="confirmation"
            )

    async def test_orbit_score_improves_with_confirmed_medications(
        self, mock_orbit_calculator
    ):
        """Confirmation → higher avg_confidence → higher total."""
        score_before = {
            "total_score": 65.0,
            "breakdown": {"avg_confidence": 70.0},
        }
        score_after = {
            "total_score": 78.0,
            "breakdown": {"avg_confidence": 90.0},
        }

        with patch("graph.orbit_score.OrbitScoreCalculator", return_value=mock_orbit_calculator):
            mock_orbit_calculator.compute.side_effect = [score_before, score_after]

            before = mock_orbit_calculator.compute(patient_id="test-patient")
            after = mock_orbit_calculator.compute(patient_id="test-patient")

            assert after["total_score"] > before["total_score"]
            assert after["breakdown"]["avg_confidence"] > before["breakdown"]["avg_confidence"]

    async def test_orbit_score_worsens_with_new_interaction(
        self, mock_orbit_calculator, mock_phig
    ):
        """New drug interaction → lower interaction_risk component."""
        score_before = {
            "total_score": 80.0,
            "breakdown": {"interaction_risk": 100.0},
        }

        mock_phig.get_interactions.return_value = [
            {"drug_pair": "Metformin + Ibuprofen", "severity": "ELEVATED"}
        ]

        score_after = {
            "total_score": 68.0,
            "breakdown": {"interaction_risk": 50.0},
        }

        with patch("graph.orbit_score.OrbitScoreCalculator", return_value=mock_orbit_calculator):
            mock_orbit_calculator.compute.side_effect = [score_before, score_after]

            before = mock_orbit_calculator.compute(patient_id="test-patient")
            after = mock_orbit_calculator.compute(patient_id="test-patient")

            assert after["total_score"] < before["total_score"]
            assert after["breakdown"]["interaction_risk"] < before["breakdown"]["interaction_risk"]

    async def test_appointment_brief_references_orbit_context(
        self, mock_previsit_agent, patient_ramesh
    ):
        """Pre-visit brief includes patient medication/lab data."""
        with patch("agents.previsit_agent.PreVisitAgent", return_value=mock_previsit_agent):
            brief = await mock_previsit_agent.generate_previsit_brief(
                patient_id=patient_ramesh["id"],
                appointment_id="appt-1"
            )

            assert "tell_doctor" in brief
            assert "ask_doctor" in brief
            assert "doctor_may_not_know" in brief
            assert "bring_to_appointment" in brief
            assert "urgency_flags" in brief

            all_text = str(brief).lower()
            assert "metformin" in all_text or len(brief["tell_doctor"]) > 0

    async def test_narrative_generated_on_document_upload(
        self, mock_narrative_agent, patient_ramesh
    ):
        """Document upload triggers living narrative creation."""
        with patch("agents.history_agent.HistoryAgent", return_value=mock_narrative_agent):
            narrative = await mock_narrative_agent.generate_living_narrative(
                patient_id=patient_ramesh["id"],
                patient_name=patient_ramesh["name"],
                trigger_event="document_upload",
                language="en"
            )

            assert isinstance(narrative, str)
            assert len(narrative) > 0
            mock_narrative_agent.generate_living_narrative.assert_called_once_with(
                patient_id=patient_ramesh["id"],
                patient_name="Ramesh Kumar",
                trigger_event="document_upload",
                language="en"
            )

    async def test_narrative_updated_on_confirmation(
        self, mock_narrative_agent, patient_ramesh
    ):
        """Confirmation → narrative regenerated with new trigger."""
        with patch("agents.history_agent.HistoryAgent", return_value=mock_narrative_agent):
            mock_narrative_agent.generate_living_narrative.return_value = (
                "Ramesh Kumar confirmed medication Metformin, increasing health profile confidence."
            )

            narrative = await mock_narrative_agent.generate_living_narrative(
                patient_id=patient_ramesh["id"],
                patient_name=patient_ramesh["name"],
                trigger_event="confirmation",
                language="en"
            )

            assert isinstance(narrative, str)
            assert len(narrative) > 0
            mock_narrative_agent.generate_living_narrative.assert_called_with(
                patient_id=patient_ramesh["id"],
                patient_name="Ramesh Kumar",
                trigger_event="confirmation",
                language="en"
            )

    async def test_orbit_history_accumulates_over_events(
        self, mock_orbit_calculator
    ):
        """Multiple events → growing orbit_score_history list."""
        scores = [
            {"total_score": 45.0, "computed_at": "2026-01-15T10:00:00Z", "delta": None},
            {"total_score": 55.0, "computed_at": "2026-01-15T11:00:00Z", "delta": 10.0},
            {"total_score": 62.0, "computed_at": "2026-01-15T12:00:00Z", "delta": 7.0},
            {"total_score": 78.0, "computed_at": "2026-01-15T13:00:00Z", "delta": 16.0},
        ]

        with patch("graph.orbit_score.OrbitScoreCalculator", return_value=mock_orbit_calculator):
            mock_orbit_calculator.compute.side_effect = scores
            history = []

            for i in range(4):
                score = mock_orbit_calculator.compute(patient_id="test-patient")
                history.append(score)

            assert len(history) == 4
            assert history[0]["delta"] is None
            for i in range(1, len(history)):
                assert history[i]["delta"] is not None
                assert history[i]["delta"] > 0
            assert history[-1]["total_score"] > history[0]["total_score"]
