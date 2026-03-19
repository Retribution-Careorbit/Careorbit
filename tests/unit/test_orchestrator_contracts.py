import pytest

from agents.contracts import InteractionAlertContract, CareGapContract
from agents.orchestrator import Orchestrator


class TestOrchestratorContracts:
    def test_interaction_contract_accepts_valid_payload(self):
        payload = {
            "drug_pair": "Metformin + Ibuprofen",
            "severity": "elevated",
            "description": "Renal stress risk",
            "clinical_action": "Monitor renal panel",
            "acknowledged": False,
        }
        model = InteractionAlertContract.model_validate(payload)
        assert model.severity == "ELEVATED"

    def test_interaction_contract_rejects_invalid_severity(self):
        payload = {
            "drug_pair": "A + B",
            "severity": "CRITICAL_PLUS",
            "description": "test",
        }
        with pytest.raises(Exception):
            InteractionAlertContract.model_validate(payload)

    def test_care_gap_contract_rejects_invalid_status(self):
        payload = {
            "name": "Retina screening",
            "status": "pending_review",
        }
        with pytest.raises(Exception):
            CareGapContract.model_validate(payload)

    def test_orchestrator_filters_invalid_payloads(self):
        raw = [
            {
                "drug_pair": "Metformin + Ibuprofen",
                "severity": "ELEVATED",
                "description": "renal risk",
                "clinical_action": "monitor",
            },
            {
                "drug_pair": "Bad pair",
                "severity": "INVALID",
                "description": "invalid",
            },
        ]

        validated = Orchestrator._validate_interactions(raw)
        assert len(validated) == 1
        assert validated[0]["severity"] == "ELEVATED"


class TestOrchestratorDeterminism:
    def test_grounded_text_is_deterministic(self):
        orchestrator = Orchestrator()
        phig = {
            "medications": [{"name": "Metformin", "dosage": "500mg", "frequency": "BD"}],
            "conditions": [{"name": "Type 2 Diabetes Mellitus"}],
            "labs": [{"name": "HbA1c", "value": 8.1, "unit": "%"}],
            "interactions": [{"drug_pair": "Metformin + Ibuprofen", "severity": "ELEVATED"}],
            "care_gaps": [{"name": "Retinopathy Screening", "status": "open"}],
        }

        outputs = [
            orchestrator._build_grounded_text("give me health overview", phig)
            for _ in range(10)
        ]

        assert all(text == outputs[0] for text in outputs)
