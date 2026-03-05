import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from graph.orbit_score import WEIGHTS, OrbitScoreCalculator


class TestOrbitWeightsConfiguration:
    """Validate that orbit score WEIGHTS match business rules."""

    def test_weights_sum_to_one(self):
        """Sum of all component weights must equal 1.0."""
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_weight_completeness_is_025(self):
        """Completeness weight must be 0.25 per business spec."""
        assert WEIGHTS["completeness"] == 0.25

    def test_weight_avg_confidence_is_020(self):
        """Average confidence weight must be 0.20 per business spec."""
        assert WEIGHTS["avg_confidence"] == 0.20

    def test_weight_interaction_risk_is_025(self):
        """Interaction risk weight must be 0.25 per business spec."""
        assert WEIGHTS["interaction_risk"] == 0.25

    def test_weight_care_gap_status_is_020(self):
        """Care gap status weight must be 0.20 per business spec."""
        assert WEIGHTS["care_gap_status"] == 0.20

    def test_weight_adherence_rate_is_010(self):
        """Adherence rate weight must be 0.10 per business spec."""
        assert WEIGHTS["adherence_rate"] == 0.10


class TestOrbitScoreBoundaryConditions:
    """Validate orbit score total boundaries using the calculator."""

    def test_perfect_patient_score_is_100(self):
        """All components at maximum should yield total_score = 100."""
        components = {
            "completeness": 100.0,
            "avg_confidence": 100.0,
            "interaction_risk": 100.0,
            "care_gap_status": 100.0,
            "adherence_rate": 100.0,
        }
        total = sum(WEIGHTS[k] * v for k, v in components.items())
        assert abs(total - 100.0) < 1e-9

    def test_worst_case_patient_score_near_zero(self):
        """All components at minimum should yield total_score near 0."""
        components = {
            "completeness": 0.0,
            "avg_confidence": 0.0,
            "interaction_risk": 0.0,
            "care_gap_status": 0.0,
            "adherence_rate": 0.0,
        }
        total = sum(WEIGHTS[k] * v for k, v in components.items())
        assert total == pytest.approx(0.0, abs=1e-9)
