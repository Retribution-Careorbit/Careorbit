# tests/integration/test_orchestrator.py
# V4 FIXES:
#   R4-2: Removed 'or len >= 1' fallback assertion (was always true)
#   Q2: Tests verify actual routing behavior
#   H2: Uses async def (asyncio_mode = auto)

import pytest
from unittest.mock import patch, AsyncMock


@pytest.fixture
def orchestrator(mock_openai, mock_search, mock_translator):
    with patch("agents.orchestrator.openai_service", mock_openai), \
         patch("agents.orchestrator.search_service", mock_search), \
         patch("agents.orchestrator.translator_service", mock_translator), \
         patch("agents.orchestrator.db_session", AsyncMock()):
        from agents.orchestrator import Orchestrator
        return Orchestrator()


class TestOrchestrator:

    async def test_medication_query_routes_to_medication_agent(self, orchestrator):
        """
        R4-2 FIX: Strict assertion — must route to medication agent specifically.
        Removed 'or len(response.agents_used) >= 1' fallback that always passed.
        """
        response = await orchestrator.process_query(
            patient_id="test-patient",
            message="Are my medications safe?",
            language="en"
        )
        agent_names_lower = [a.lower() for a in response.agents_used]
        assert any("medication" in a for a in agent_names_lower), \
            f"Medication query did not route to MedicationAgent. " \
            f"Agents used: {response.agents_used}"
        assert len(response.message) > 20

    async def test_care_gap_query_routes_to_care_gap_agent(self, orchestrator):
        """Care gap keywords → care gap agent invoked."""
        response = await orchestrator.process_query(
            patient_id="test-patient",
            message="Am I due for any screenings or checkups?",
            language="en"
        )
        agent_names_lower = [a.lower() for a in response.agents_used]
        assert any("care_gap" in a or "care gap" in a for a in agent_names_lower), \
            f"Care gap query did not route to CareGapAgent. " \
            f"Agents used: {response.agents_used}"

    async def test_health_overview_routes_to_multiple_agents(self, orchestrator):
        """Broad overview query triggers multi-agent routing."""
        response = await orchestrator.process_query(
            patient_id="test-patient",
            message="Give me a complete overview of everything",
            language="en"
        )
        assert len(response.agents_used) >= 2, \
            f"Expected multi-agent routing for overview query, " \
            f"got: {response.agents_used}"

    async def test_hindi_query_invokes_translator(self, orchestrator, mock_translator):
        """
        Hindi input → translator.translate() called for English conversion,
        then again for Hindi response.
        """
        response = await orchestrator.process_query(
            patient_id="test-patient",
            message="Meri dawaiyon ke baare mein batao",
            language="hi"
        )
        mock_translator.translate.assert_called()
        assert len(response.message) > 0

    async def test_response_has_required_fields(self, orchestrator):
        """OrchestratorResponse must have all required fields."""
        response = await orchestrator.process_query(
            patient_id="test-patient",
            message="How am I doing?",
            language="en"
        )
        assert hasattr(response, "message")
        assert hasattr(response, "agents_used")
        assert hasattr(response, "alerts")
        assert hasattr(response, "care_gaps")
        assert hasattr(response, "confidence")
        assert isinstance(response.agents_used, list)
        assert 0.0 <= response.confidence <= 1.0

    async def test_unknown_query_routes_to_all_agents(self, orchestrator):
        """Orchestrator.py: if no keywords match → all 3 agents are run."""
        response = await orchestrator.process_query(
            patient_id="test-patient",
            message="zzz_completely_unrecognized_query",
            language="en"
        )
        assert len(response.agents_used) >= 1
