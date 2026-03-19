import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.helpers.mocks import MockDBSession

from graph.orbit_score import OrbitScoreCalculator, WEIGHTS


class TestCompletenessComponent:

    def test_completeness_all_node_types_present(self):
        phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin", "phig_node_id": "m1"},
                {"type": "condition", "name": "Hypertension", "icd10": "I10", "phig_node_id": "c1"},
                {"type": "lab_value", "name": "Creatinine", "value": 1.1, "phig_node_id": "l1"},
            ],
            "edges": [
                {"edge_type": "CONDITION_HAS_MEDICATION", "source_node_id": "c1", "target_node_id": "m1", "source_node_type": "condition", "target_node_type": "medication"},
                {"edge_type": "CONDITION_HAS_LAB", "source_node_id": "c1", "target_node_id": "l1", "source_node_type": "condition", "target_node_type": "lab_result"},
            ],
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_completeness()
        assert score == 100.0

    def test_completeness_partial_node_types(self):
        phig = {
            "nodes": [
                {"type": "medication", "name": "Amlodipine", "phig_node_id": "m1"},
                {"type": "condition", "name": "Hypertension", "icd10": "I10", "phig_node_id": "c1"},
            ],
            "edges": [
                {"edge_type": "CONDITION_HAS_MEDICATION", "source_node_id": "c1", "target_node_id": "m1", "source_node_type": "condition", "target_node_type": "medication"},
            ],
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_completeness()
        assert score == 50.0

    def test_completeness_no_nodes(self):
        phig = {"nodes": []}
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_completeness()
        assert score == 0.0

    def test_completeness_bonus_care_gap_nodes(self):
        phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin", "phig_node_id": "m1"},
                {"type": "condition", "name": "Type 2 Diabetes Mellitus", "icd10": "E11.9", "phig_node_id": "c1"},
                {"type": "lab_value", "name": "HbA1c", "value": 7.8, "phig_node_id": "l1"},
                {"type": "lab_value", "name": "Creatinine", "value": 1.4, "phig_node_id": "l2"},
                {"type": "care_gap", "name": "Retinopathy Screening"},
            ],
            "edges": [
                {"edge_type": "CONDITION_HAS_MEDICATION", "source_node_id": "c1", "target_node_id": "m1", "source_node_type": "condition", "target_node_type": "medication"},
                {"edge_type": "CONDITION_HAS_LAB", "source_node_id": "c1", "target_node_id": "l1", "source_node_type": "condition", "target_node_type": "lab_result"},
                {"edge_type": "CONDITION_HAS_LAB", "source_node_id": "c1", "target_node_id": "l2", "source_node_type": "condition", "target_node_type": "lab_result"},
            ],
            "care_gaps": [
                {"condition_code": "E11.9", "status": "resolved"}
            ],
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_completeness()
        assert score >= 100.0
        base_phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin"},
                {"type": "condition", "name": "Diabetes"},
                {"type": "lab_value", "name": "HbA1c", "value": 7.8},
            ]
        }
        base_calc = OrbitScoreCalculator(base_phig)
        base_score = base_calc._compute_completeness()
        assert score >= base_score

    def test_completeness_bonus_provider_nodes(self):
        phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin"},
                {"type": "condition", "name": "Diabetes"},
                {"type": "lab_value", "name": "HbA1c", "value": 7.8},
                {"type": "provider", "name": "Dr. Roy"},
            ]
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_completeness()
        base_phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin"},
                {"type": "condition", "name": "Diabetes"},
                {"type": "lab_value", "name": "HbA1c", "value": 7.8},
            ]
        }
        base_calc = OrbitScoreCalculator(base_phig)
        base_score = base_calc._compute_completeness()
        assert score >= base_score

    def test_completeness_capped_at_100(self):
        phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin"},
                {"type": "condition", "name": "Diabetes"},
                {"type": "lab_value", "name": "HbA1c", "value": 7.8},
                {"type": "care_gap", "name": "Retinopathy Screening"},
                {"type": "provider", "name": "Dr. Roy"},
            ]
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_completeness()
        assert score <= 100.0


class TestAvgConfidenceComponent:

    def test_avg_confidence_medication_nodes(self):
        phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin", "confidence": 0.85},
                {"type": "medication", "name": "Amlodipine", "confidence": 0.90},
            ]
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_avg_confidence()
        expected = ((0.85 + 0.90) / 2) * 100
        assert abs(score - expected) < 0.1

    def test_avg_confidence_no_medications(self):
        phig = {
            "nodes": [
                {"type": "condition", "name": "Diabetes"},
            ]
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_avg_confidence()
        assert score == 0.0


class TestInteractionRiskComponent:

    def test_interaction_risk_no_interactions(self):
        phig = {"nodes": [], "interactions": []}
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_interaction_risk()
        assert score == 100.0

    def test_interaction_risk_elevated_penalty(self):
        phig = {
            "nodes": [],
            "interactions": [
                {"severity": "ELEVATED", "acknowledged": False},
            ]
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_interaction_risk()
        assert score == 75.0

    def test_interaction_risk_moderate_penalty(self):
        phig = {
            "nodes": [],
            "interactions": [
                {"severity": "Moderate", "acknowledged": False},
            ]
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_interaction_risk()
        assert score == 85.0

    def test_interaction_risk_low_penalty(self):
        phig = {
            "nodes": [],
            "interactions": [
                {"severity": "Low", "acknowledged": False},
            ]
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_interaction_risk()
        assert score == 95.0

    def test_interaction_risk_resolved_half_penalty(self):
        phig = {
            "nodes": [],
            "interactions": [
                {"severity": "ELEVATED", "acknowledged": True},
            ]
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_interaction_risk()
        unresolved_phig = {
            "nodes": [],
            "interactions": [
                {"severity": "ELEVATED", "acknowledged": False},
            ]
        }
        unresolved_calc = OrbitScoreCalculator(unresolved_phig)
        unresolved_score = unresolved_calc._compute_interaction_risk()
        assert score > unresolved_score
        expected = 100.0 - (25 * 0.5)
        assert abs(score - expected) < 0.1

    def test_interaction_risk_floor_at_zero(self):
        phig = {
            "nodes": [],
            "interactions": [
                {"severity": "ELEVATED", "acknowledged": False},
                {"severity": "ELEVATED", "acknowledged": False},
                {"severity": "ELEVATED", "acknowledged": False},
                {"severity": "ELEVATED", "acknowledged": False},
                {"severity": "ELEVATED", "acknowledged": False},
            ]
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_interaction_risk()
        assert score >= 0.0


class TestCareGapComponent:

    def test_care_gap_no_open_gaps(self):
        phig = {
            "nodes": [],
            "care_gaps": [],
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_care_gap_status()
        assert score == 100.0

    def test_care_gap_each_open_gap_minus_20(self):
        phig = {
            "nodes": [],
            "care_gaps": [
                {"name": "Gap 1", "status": "open"},
                {"name": "Gap 2", "status": "open"},
                {"name": "Gap 3", "status": "open"},
            ],
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_care_gap_status()
        assert abs(score - 40.0) < 0.1

    def test_care_gap_floor_at_zero(self):
        phig = {
            "nodes": [],
            "care_gaps": [
                {"name": f"Gap {i}", "status": "open"} for i in range(6)
            ],
        }
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_care_gap_status()
        assert score == 0.0


class TestAdherenceComponent:

    def test_adherence_rate_calculation(self):
        reminders = {
            "taken": 8,
            "skipped": 1,
            "no_response": 1,
        }
        phig = {"nodes": [], "reminders": reminders}
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_adherence_rate()
        expected = (8 / (8 + 1 + 1)) * 100
        assert abs(score - expected) < 0.1

    def test_adherence_no_reminders_neutral_75(self):
        phig = {"nodes": []}
        calc = OrbitScoreCalculator(phig)
        score = calc._compute_adherence_rate()
        assert score == 75.0


class TestTotalScore:

    def test_total_score_weighted_sum(self):
        phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin", "confidence": 0.85},
                {"type": "condition", "name": "Diabetes"},
                {"type": "lab_value", "name": "HbA1c", "value": 7.8},
            ],
            "interactions": [],
            "care_gaps": [],
        }
        calc = OrbitScoreCalculator(phig)
        result = calc.compute()

        completeness = calc._compute_completeness()
        avg_confidence = calc._compute_avg_confidence()
        interaction_risk = calc._compute_interaction_risk()
        care_gap_status = calc._compute_care_gap_status()
        adherence_rate = calc._compute_adherence_rate()

        expected = (
            WEIGHTS["completeness"] * completeness +
            WEIGHTS["avg_confidence"] * avg_confidence +
            WEIGHTS["interaction_risk"] * interaction_risk +
            WEIGHTS["care_gap_status"] * care_gap_status +
            WEIGHTS["adherence_rate"] * adherence_rate
        )
        assert abs(result["total_score"] - expected) < 0.1

    def test_total_score_range_0_to_100(self):
        for nodes in [[], [{"type": "medication", "name": "X", "confidence": 0.5}]]:
            phig = {"nodes": nodes, "interactions": [], "care_gaps": []}
            calc = OrbitScoreCalculator(phig)
            result = calc.compute()
            assert 0 <= result["total_score"] <= 100


class TestDeltaComputation:

    def test_delta_computation_vs_previous(self):
        phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin", "confidence": 0.85},
                {"type": "condition", "name": "Diabetes"},
                {"type": "lab_value", "name": "HbA1c", "value": 7.8},
            ],
            "interactions": [],
            "care_gaps": [],
        }
        calc = OrbitScoreCalculator(phig)
        result = calc.compute()
        current = result["total_score"]

        previous_score = 60.0
        delta = calc.compute_delta(previous_score)
        assert abs(delta - (current - previous_score)) < 0.1

    def test_delta_none_if_first_score(self):
        phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin", "confidence": 0.85},
            ],
            "interactions": [],
            "care_gaps": [],
        }
        calc = OrbitScoreCalculator(phig)
        delta = calc.compute_delta(None)
        assert delta is None


class TestOrbitScorePersistence:

    @pytest.mark.asyncio
    async def test_orbit_score_saved_to_history(self):
        mock_db = MockDBSession()
        mock_db.seed("orbit_score_history", [])

        phig = {
            "nodes": [
                {"type": "medication", "name": "Metformin", "confidence": 0.85},
                {"type": "condition", "name": "Diabetes"},
                {"type": "lab_value", "name": "HbA1c", "value": 7.8},
            ],
            "interactions": [],
            "care_gaps": [],
        }
        calc = OrbitScoreCalculator(phig)
        result = calc.compute()

        patient_id = "test-patient-id"
        await calc.save_to_history(mock_db, patient_id, result["total_score"])

        mock_db.assert_query_contains("orbit_score_history")
        mock_db.assert_param_value("patient_id", patient_id)
