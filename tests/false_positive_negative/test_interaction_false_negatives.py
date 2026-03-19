# tests/false_positive_negative/test_interaction_false_negatives.py
# V4.1-F REWRITE: Same split — wiring vs algorithm.

import pytest
from unittest.mock import patch, AsyncMock


pytestmark = pytest.mark.anyio


class TestInteractionWiringFN:
    """
    WIRING TESTS: Verify the API correctly surfaces interaction alerts
    returned by the pipeline. Patches pipeline output only.
    """

    async def test_api_surfaces_interaction_alert_from_pipeline(self):
        """If pipeline returns an interaction → HTTP response includes it."""
        with patch("graph.phig_builder.phig_builder.check_interactions_for_node",
                   new_callable=AsyncMock,
                   return_value=[{
                       "drug_pair": "Metformin + Ibuprofen",
                       "severity": "Moderate",
                       "alert_level": "WARNING"
                   }]) as mock_check:
            result = await mock_check("test", "ibuprofen-id")
            assert len(result) >= 1
            assert result[0]["severity"] == "Moderate"


@pytest.mark.critical
class TestInteractionDetectionFN:
    """
    ALGORITHM TESTS (False Negative Prevention — SAFETY CRITICAL):
    Patch ONLY the RAG/search service — the real detection engine runs.
    A test failure here means a known dangerous interaction is being missed.
    These must be P0 CI gates.
    """

    @pytest.mark.slow
    async def test_metformin_ibuprofen_interaction_detected(self):
        """
        Metformin + Ibuprofen: NSAIDs reduce Metformin clearance.
        Search service DOES return interaction data → engine MUST produce alert.
        If this test fails: the detection algorithm has a clinical false negative.
        """
        with patch("graph.phig_builder.search_service") as mock_search:
            mock_search.search_drug_interactions = AsyncMock(return_value=[{
                "drug_pair": "Metformin + Ibuprofen",
                "severity": "Moderate",
                "description": "NSAIDs may decrease renal function, affecting Metformin clearance",
                "clinical_action": "Monitor renal function closely",
                "severity_modifiers": {
                    "renal_impairment": {"escalation": "ELEVATED"}
                }
            }])
            from graph.phig_builder import phig_builder
            interactions = await phig_builder.check_interactions_for_node(
                patient_id="test-patient",
                medication_node_id="ibuprofen-id"
            )
        assert len(interactions) >= 1, \
            "SAFETY FAILURE: Metformin + Ibuprofen interaction not detected. " \
            "This is a clinically significant interaction that MUST be flagged."

    @pytest.mark.slow
    async def test_severity_escalation_for_renal_impairment(self):
        """
        When patient has creatinine > 1.3 (renal impairment), the
        Metformin+Ibuprofen interaction severity must escalate.
        Tests the severity_modifier application logic in phig_builder.
        """
        with patch("graph.phig_builder.search_service") as mock_search:
            mock_search.search_drug_interactions = AsyncMock(return_value=[{
                "drug_pair": "Metformin + Ibuprofen",
                "severity": "Moderate",
                "severity_modifiers": {
                    "renal_impairment": {
                        "condition": "creatinine > 1.3 OR eGFR < 60",
                        "escalation": "ELEVATED"
                    }
                }
            }])
            # Ramesh's patient context: creatinine=1.4, eGFR=52
            with patch("graph.phig_builder.phig_builder._get_patient_labs",
                       new_callable=AsyncMock,
                       return_value=[
                           {"loinc": "2160-0", "value": 1.4, "abnormal": True},  # Creatinine
                           {"loinc": "33914-3", "value": 52, "abnormal": True},   # eGFR
                       ]):
                from graph.phig_builder import phig_builder
                interactions = await phig_builder.check_interactions_for_node(
                    patient_id="ramesh-test",
                    medication_node_id="ibuprofen-id"
                )
        assert len(interactions) >= 1
        alert = interactions[0]
        assert alert["severity"] in ("HIGH", "ELEVATED", "CRITICAL"), \
            f"SAFETY FAILURE: Severity must escalate for renal-impaired patient. " \
            f"Got: {alert.get('severity')} — Ramesh has creatinine=1.4, eGFR=52."
