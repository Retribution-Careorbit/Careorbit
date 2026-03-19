# tests/unit/test_confidence_scoring.py
# V4 FIXES:
#   C2: Removed 'or True' (was V3 fix; preserved)
#   H5: Ceiling iteration restricted to PHASE1_SOURCES
#   V4-6: Removed TestSourceCeilingsPhase2 (speculative values, not in spec)
#   V4-11: Strengthened determinism test to check component-level counts

import pytest
from graph.confidence import ConfidenceCalculator, ConfidenceBreakdown
from tests.conftest import PHASE1_SOURCES


class TestSourceCeilingsPhase1:
    """Validate hardcoded ceiling values for all Phase 1 input sources."""

    def test_prescription_photo_ceiling(self):
        assert ConfidenceCalculator.SOURCE_CEILINGS["prescription_photo"] == 0.85

    def test_lab_report_photo_ceiling(self):
        assert ConfidenceCalculator.SOURCE_CEILINGS["lab_report_photo"] == 0.88

    def test_medicine_strip_photo_ceiling(self):
        assert ConfidenceCalculator.SOURCE_CEILINGS["medicine_strip_photo"] == 0.90

    def test_patient_text_input_ceiling(self):
        assert ConfidenceCalculator.SOURCE_CEILINGS["patient_text_input"] == 0.60

    @pytest.mark.skip(reason="patient_confirmed ceiling not yet defined in MVP spec")
    def test_patient_confirmed_ceiling(self):
        """Deferred: ceiling value undefined until patient confirmation spec is finalised."""
        assert "patient_confirmed" in ConfidenceCalculator.SOURCE_CEILINGS

    def test_all_phase1_ceilings_in_valid_range(self):
        for source in PHASE1_SOURCES:
            ceiling = ConfidenceCalculator.SOURCE_CEILINGS[source]
            assert 0.0 < ceiling <= 1.0, \
                f"Ceiling for '{source}' out of valid range (0,1]: {ceiling}"

    def test_phase1_ranking_order(self):
        """Medicine strip > lab report > prescription > patient text — from spec."""
        c = ConfidenceCalculator.SOURCE_CEILINGS
        assert c["medicine_strip_photo"] >= c["lab_report_photo"]
        assert c["lab_report_photo"] >= c["prescription_photo"]
        assert c["prescription_photo"] >= c["patient_text_input"]

    def test_no_unexpected_phase1_sources_in_ceilings(self):
        """
        V4 ADD: If a new source is added to SOURCE_CEILINGS, this test forces
        the developer to also add it to PHASE1_SOURCES or PHASE2_SOURCES.
        Prevents silent Phase 2 source contamination.

        V4.1-E: patient_confirmed / patient_corrected are Phase 1 sources
        (used in confirmations.py). They bypass ConfidenceCalculator ceilings —
        the confirmation route sets score=0.85 directly. They are listed in
        PHASE1_SOURCES but should NOT appear in SOURCE_CEILINGS (no ceiling
        is needed because the score is hardcoded, not calculated).
        """
        known_all_sources = set(PHASE1_SOURCES) | {
            # Phase 2 sources (no ceiling defined yet — speculative):
            "fhir_api", "doctor_portal", "voice_input",
            # Digital ingestion sources currently emitted by document_pipeline for PDFs.
            "prescription_digital", "lab_report_digital",
        }
        for source in ConfidenceCalculator.SOURCE_CEILINGS:
            assert source in known_all_sources, (
                f"Unknown source '{source}' in SOURCE_CEILINGS. "
                f"Add it to PHASE1_SOURCES (with ceiling test) or the Phase 2 known_set."
            )


@pytest.mark.phase2
@pytest.mark.skip(reason="Phase 2 source ceiling values not yet specified in design doc")
class TestSourceCeilingsPhase2:
    """
    V4-6: REMOVED speculative ceiling values (fhir_api=0.95, doctor_portal=0.95,
    patient_voice_input=0.55 were never defined in any spec document).
    Placeholder class preserved for when Phase 2 ceilings are formally specified.
    """
    pass


class TestMedicationConfidence:
    """Core confidence calculation tests."""

    def test_perfect_prescription_photo(self):
        result = ConfidenceCalculator.calculate_medication_confidence(
            source_type="prescription_photo",
            ocr_avg_confidence=0.98, drug_match_score=1.0,
            dosage_parsed=True, date_found=True, patient_confirmed=True
        )
        assert result.final_score <= 0.85
        assert result.final_score >= 0.80
        assert result.confidence_label == "VERIFIED"

    def test_score_never_exceeds_source_ceiling(self):
        """V3 FIX H5: Only iterate Phase 1 sources."""
        for source_type in PHASE1_SOURCES:
            ceiling = ConfidenceCalculator.SOURCE_CEILINGS[source_type]
            result = ConfidenceCalculator.calculate_medication_confidence(
                source_type=source_type,
                ocr_avg_confidence=1.0, drug_match_score=1.0,
                dosage_parsed=True, date_found=True, patient_confirmed=True
            )
            assert result.final_score <= ceiling, (
                f"{source_type}: score {result.final_score} exceeds ceiling {ceiling}"
            )

    def test_score_never_negative(self):
        result = ConfidenceCalculator.calculate_medication_confidence(
            source_type="patient_text_input",
            ocr_avg_confidence=0.0, drug_match_score=0.0,
            dosage_parsed=False, date_found=False, patient_confirmed=False
        )
        assert result.final_score >= 0.0

    # V4.1-D REMOVED: test_score_never_below_minimum_threshold
    # That test asserted >= 0.0 (identical to test_score_never_negative above)
    # while its comment claimed a "0.05 minimum floor" — a value that does not
    # exist anywhere in the MVP codebase. Removed to avoid false confidence
    # and misleading spec claims.

    def test_breakdown_factors_are_reproducible(self):
        """
        V4-11: Strengthened — verifies score AND breakdown component count
        across 10 identical calls. Catches non-determinism at both levels.
        """
        results = []
        for _ in range(10):
            r = ConfidenceCalculator.calculate_medication_confidence(
                source_type="prescription_photo",
                ocr_avg_confidence=0.92, drug_match_score=0.88,
                dosage_parsed=True, date_found=True, patient_confirmed=False
            )
            results.append(r)

        scores = [r.final_score for r in results]
        assert all(s == scores[0] for s in scores), \
            f"Non-deterministic scores: {set(scores)}"

        # Also verify breakdown structure is stable (not just final score)
        if hasattr(results[0], 'breakdown') and results[0].breakdown:
            first_breakdown = results[0].breakdown
            for r in results[1:]:
                assert r.breakdown == first_breakdown, \
                    "Breakdown factors are non-deterministic"

    def test_patient_confirmation_boosts_confidence(self):
        without_confirm = ConfidenceCalculator.calculate_medication_confidence(
            source_type="prescription_photo",
            ocr_avg_confidence=0.80, drug_match_score=0.85,
            dosage_parsed=True, date_found=True, patient_confirmed=False
        )
        with_confirm = ConfidenceCalculator.calculate_medication_confidence(
            source_type="prescription_photo",
            ocr_avg_confidence=0.80, drug_match_score=0.85,
            dosage_parsed=True, date_found=True, patient_confirmed=True
        )
        # Confirmation should improve or equal score (up to ceiling)
        assert with_confirm.final_score >= without_confirm.final_score

    def test_low_ocr_confidence_lowers_score(self):
        high_ocr = ConfidenceCalculator.calculate_medication_confidence(
            source_type="prescription_photo",
            ocr_avg_confidence=0.95, drug_match_score=0.90,
            dosage_parsed=True, date_found=True, patient_confirmed=False
        )
        low_ocr = ConfidenceCalculator.calculate_medication_confidence(
            source_type="prescription_photo",
            ocr_avg_confidence=0.35, drug_match_score=0.90,
            dosage_parsed=True, date_found=True, patient_confirmed=False
        )
        assert low_ocr.final_score < high_ocr.final_score

    def test_missing_drug_match_lowers_score(self):
        known_drug = ConfidenceCalculator.calculate_medication_confidence(
            source_type="prescription_photo",
            ocr_avg_confidence=0.92, drug_match_score=1.0,
            dosage_parsed=True, date_found=True, patient_confirmed=False
        )
        unknown_drug = ConfidenceCalculator.calculate_medication_confidence(
            source_type="prescription_photo",
            ocr_avg_confidence=0.92, drug_match_score=0.0,
            dosage_parsed=True, date_found=True, patient_confirmed=False
        )
        assert unknown_drug.final_score < known_drug.final_score


class TestLabConfidence:
    """Lab report confidence scoring."""

    def test_perfect_lab_report(self):
        result = ConfidenceCalculator.calculate_lab_confidence(
            source_type="lab_report_photo",
            ocr_avg_confidence=0.97, value_parsed=True,
            unit_recognized=True, reference_range_found=True,
            patient_confirmed=False
        )
        assert result.final_score <= 0.88
        assert result.final_score >= 0.82

    def test_lab_score_never_exceeds_ceiling(self):
        result = ConfidenceCalculator.calculate_lab_confidence(
            source_type="lab_report_photo",
            ocr_avg_confidence=1.0, value_parsed=True,
            unit_recognized=True, reference_range_found=True,
            patient_confirmed=True
        )
        assert result.final_score <= ConfidenceCalculator.SOURCE_CEILINGS["lab_report_photo"]
