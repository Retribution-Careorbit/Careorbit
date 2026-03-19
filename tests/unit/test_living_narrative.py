import pytest
from unittest.mock import patch, AsyncMock, MagicMock


pytestmark = pytest.mark.anyio


@pytest.fixture
def mock_phig_nodes():
    return [
        {"type": "medication", "name": "Metformin", "dosage": "500mg BD", "confidence": 0.85},
        {"type": "medication", "name": "Amlodipine", "dosage": "5mg OD", "confidence": 0.82},
        {"type": "condition", "name": "Type 2 Diabetes Mellitus", "code": "E11.9", "confidence": 0.85},
        {"type": "lab_value", "name": "HbA1c", "value": 7.8, "unit": "%", "confidence": 0.90},
    ]


@pytest.fixture
def history_agent(mock_openai, mock_translator, mock_db):
    with patch("agents.history_agent.openai_service", mock_openai), \
         patch("agents.history_agent.translator_service", mock_translator), \
         patch("agents.history_agent.db_session", mock_db):
        from agents.history_agent import generate_living_narrative
        yield generate_living_narrative


class TestLivingNarrative:

    async def test_narrative_returns_nonempty_string(self, history_agent, mock_phig_nodes):
        result = await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="document_upload",
            language="en",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_narrative_trigger_document_upload(self, history_agent, mock_phig_nodes):
        result = await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="document_upload",
            language="en",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_narrative_trigger_confirmation(self, history_agent, mock_phig_nodes):
        result = await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="confirmation",
            language="en",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_narrative_trigger_lab_added(self, history_agent, mock_phig_nodes):
        result = await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="lab_added",
            language="en",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_narrative_trigger_interaction_detected(self, history_agent, mock_phig_nodes):
        result = await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="interaction_detected",
            language="en",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_narrative_saved_to_health_narratives_table(self, history_agent, mock_phig_nodes, mock_db):
        await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="document_upload",
            language="en",
        )
        mock_db.assert_query_contains("health_narratives")
        mock_db.assert_query_contains("insert")

    async def test_narrative_hindi_version_stored(self, history_agent, mock_phig_nodes, mock_db):
        await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="document_upload",
            language="hi",
        )
        found_hindi = False
        for _, params in mock_db._execute_history:
            if params and isinstance(params, dict) and params.get("narrative_text_hi") is not None:
                found_hindi = True
                break
        assert found_hindi, "Hindi narrative text should be populated when language='hi'"

    async def test_narrative_english_no_hindi_field(self, history_agent, mock_phig_nodes, mock_db):
        await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="document_upload",
            language="en",
        )
        for _, params in mock_db._execute_history:
            if params and isinstance(params, dict) and "narrative_text_hi" in params:
                assert params["narrative_text_hi"] is None, \
                    "narrative_text_hi should be None for English language"

    async def test_narrative_does_not_use_word_patient(self, history_agent, mock_phig_nodes):
        result = await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="document_upload",
            language="en",
        )
        assert "patient" not in result.lower(), \
            f"Narrative should not contain the word 'patient', got: {result}"

    async def test_narrative_mentions_patient_name(self, history_agent, mock_phig_nodes):
        result = await history_agent(
            patient_id="test-patient",
            patient_name="Ramesh Kumar",
            phig_nodes=mock_phig_nodes,
            trigger_event="document_upload",
            language="en",
        )
        assert "Ramesh" in result or "Kumar" in result, \
            f"Narrative should reference patient name 'Ramesh Kumar', got: {result}"
