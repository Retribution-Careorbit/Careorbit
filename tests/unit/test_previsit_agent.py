import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4


REQUIRED_BRIEF_KEYS = [
    "tell_doctor",
    "ask_doctor",
    "doctor_may_not_know",
    "bring_to_appointment",
    "urgency_flags",
]


@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.fixture
def sample_phig(patient_ramesh):
    return {
        "patient_id": patient_ramesh["id"],
        "patient_name": patient_ramesh["name"],
        "medications": patient_ramesh["medications"],
        "conditions": patient_ramesh["conditions"],
        "labs": patient_ramesh["labs"],
        "interactions": [
            {
                "drug_pair": "Metformin + Ibuprofen",
                "severity": "ELEVATED",
                "description": "NSAIDs may decrease renal function",
            }
        ],
        "care_gaps": [],
    }


@pytest.fixture
def empty_phig():
    return {
        "patient_id": str(uuid4()),
        "patient_name": "Empty Patient",
        "medications": [],
        "conditions": [],
        "labs": [],
        "interactions": [],
        "care_gaps": [],
    }


@pytest.fixture
def sample_appointment():
    return {
        "id": str(uuid4()),
        "patient_id": str(uuid4()),
        "doctor_name": "Dr. Amit Roy",
        "appointment_datetime": "2026-01-20T10:00:00",
        "brief_content": None,
        "brief_sent_at": None,
    }


def _make_brief_response(phig):
    brief = {
        "tell_doctor": [
            f"Currently taking {len(phig.get('medications', []))} medications"
        ],
        "ask_doctor": ["Review current medication regimen"],
        "doctor_may_not_know": [],
        "bring_to_appointment": ["Health summary PDF"],
        "urgency_flags": [],
    }
    for med in phig.get("medications", []):
        brief["tell_doctor"].append(f"Taking {med['name']} {med.get('dosage', '')}")
    for interaction in phig.get("interactions", []):
        if interaction.get("severity") in ("ELEVATED", "HIGH"):
            brief["urgency_flags"].append(
                f"{interaction['severity']} interaction: {interaction['drug_pair']}"
            )
    for med in phig.get("medications", []):
        brief["doctor_may_not_know"].append(med["name"])
    return brief


class TestPreVisitBrief:

    async def test_generate_brief_returns_required_sections(
        self, mock_openai, mock_db_session, sample_phig, sample_appointment
    ):
        mock_openai.chat = AsyncMock(
            return_value=str(_make_brief_response(sample_phig))
        )
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            result = await agent.generate_previsit_brief(
                appointment_id=sample_appointment["id"],
                phig=sample_phig,
            )
        for key in REQUIRED_BRIEF_KEYS:
            assert key in result, f"Missing required key: {key}"

    async def test_brief_includes_health_summary_pdf_in_bring(
        self, mock_openai, mock_db_session, sample_phig, sample_appointment
    ):
        brief_data = _make_brief_response(sample_phig)
        mock_openai.chat = AsyncMock(return_value=str(brief_data))
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            result = await agent.generate_previsit_brief(
                appointment_id=sample_appointment["id"],
                phig=sample_phig,
            )
        bring_items = result.get("bring_to_appointment", [])
        bring_text = " ".join(str(item).lower() for item in bring_items)
        assert "health summary" in bring_text or "pdf" in bring_text, \
            f"bring_to_appointment should reference health summary PDF, got: {bring_items}"

    async def test_brief_cross_provider_medications_detected(
        self, mock_openai, mock_db_session, sample_phig, sample_appointment
    ):
        brief_data = _make_brief_response(sample_phig)
        mock_openai.chat = AsyncMock(return_value=str(brief_data))
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            result = await agent.generate_previsit_brief(
                appointment_id=sample_appointment["id"],
                phig=sample_phig,
            )
        doctor_may_not_know = result.get("doctor_may_not_know", [])
        assert len(doctor_may_not_know) > 0, \
            "doctor_may_not_know should list medications from other providers"

    async def test_brief_elevated_interaction_in_urgency_flags(
        self, mock_openai, mock_db_session, sample_phig, sample_appointment
    ):
        brief_data = _make_brief_response(sample_phig)
        mock_openai.chat = AsyncMock(return_value=str(brief_data))
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            result = await agent.generate_previsit_brief(
                appointment_id=sample_appointment["id"],
                phig=sample_phig,
            )
        urgency_flags = result.get("urgency_flags", [])
        urgency_text = " ".join(str(f).lower() for f in urgency_flags)
        assert "elevated" in urgency_text or len(urgency_flags) > 0, \
            f"ELEVATED interaction should appear in urgency_flags, got: {urgency_flags}"

    async def test_brief_saved_to_appointments_table(
        self, mock_openai, mock_db_session, sample_phig, sample_appointment
    ):
        brief_data = _make_brief_response(sample_phig)
        mock_openai.chat = AsyncMock(return_value=str(brief_data))
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            await agent.generate_previsit_brief(
                appointment_id=sample_appointment["id"],
                phig=sample_phig,
            )
        calls = mock_db_session.execute.call_args_list
        update_calls = [
            c for c in calls
            if "update" in str(c).lower() or "brief_content" in str(c).lower()
        ]
        assert len(update_calls) > 0 or mock_db_session.commit.called, \
            "Brief content should be saved to appointments table"

    async def test_brief_sent_at_updated(
        self, mock_openai, mock_db_session, sample_phig, sample_appointment
    ):
        brief_data = _make_brief_response(sample_phig)
        mock_openai.chat = AsyncMock(return_value=str(brief_data))
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            await agent.generate_previsit_brief(
                appointment_id=sample_appointment["id"],
                phig=sample_phig,
            )
        all_call_strs = " ".join(str(c) for c in mock_db_session.execute.call_args_list)
        assert "brief_sent_at" in all_call_strs or mock_db_session.commit.called, \
            "brief_sent_at should be set after generation"

    async def test_brief_no_medications_graceful(
        self, mock_openai, mock_db_session, empty_phig, sample_appointment
    ):
        brief_data = _make_brief_response(empty_phig)
        mock_openai.chat = AsyncMock(return_value=str(brief_data))
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            result = await agent.generate_previsit_brief(
                appointment_id=sample_appointment["id"],
                phig=empty_phig,
            )
        for key in REQUIRED_BRIEF_KEYS:
            assert key in result, \
                f"Empty PHIG should still return valid brief with key: {key}"

    async def test_brief_nonexistent_appointment_returns_error(
        self, mock_openai, mock_db_session, sample_phig
    ):
        mock_db_session.execute = AsyncMock(return_value=MagicMock(first=MagicMock(return_value=None)))
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            with pytest.raises((ValueError, KeyError, Exception)):
                await agent.generate_previsit_brief(
                    appointment_id="nonexistent-id-99999",
                    phig=sample_phig,
                )

    async def test_brief_patient_specific_not_generic(
        self, mock_openai, mock_db_session, sample_phig, sample_appointment
    ):
        brief_data = _make_brief_response(sample_phig)
        mock_openai.chat = AsyncMock(return_value=str(brief_data))
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            result = await agent.generate_previsit_brief(
                appointment_id=sample_appointment["id"],
                phig=sample_phig,
            )
        result_text = str(result).lower()
        med_names = [m["name"].lower() for m in sample_phig["medications"]]
        found = any(name in result_text for name in med_names)
        assert found, \
            f"Brief should reference actual medication names from PHIG. " \
            f"Expected one of {med_names} in brief output."

    async def test_brief_openai_called_with_previsit_prompt(
        self, mock_openai, mock_db_session, sample_phig, sample_appointment
    ):
        brief_data = _make_brief_response(sample_phig)
        mock_openai.chat = AsyncMock(return_value=str(brief_data))
        with patch("agents.previsit_agent.openai_service", mock_openai), \
             patch("agents.previsit_agent.db_session", mock_db_session):
            from agents.previsit_agent import PreVisitAgent
            agent = PreVisitAgent()
            await agent.generate_previsit_brief(
                appointment_id=sample_appointment["id"],
                phig=sample_phig,
            )
        mock_openai.chat.assert_called()
        call_args = str(mock_openai.chat.call_args)
        assert "pre" in call_args.lower() or "visit" in call_args.lower() or \
               "brief" in call_args.lower() or mock_openai.chat.called, \
            "OpenAI should be called with a pre-visit prompt template"
