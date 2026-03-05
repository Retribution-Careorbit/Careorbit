import pytest
from unittest.mock import patch, MagicMock
from pipeline.fhir_converter import (
    medication_to_fhir,
    lab_to_fhir,
)


class TestMedicationToFHIR:

    def test_medication_to_fhir_returns_medication_statement(self):
        medication = {
            "name": "Metformin",
            "dosage": "500mg BD",
            "rxnorm": "6809",
            "confidence": 0.85,
        }
        result = medication_to_fhir(medication)
        assert isinstance(result, dict)
        assert result["resourceType"] == "MedicationStatement"

    def test_medication_to_fhir_includes_rxnorm_coding(self):
        medication = {
            "name": "Metformin",
            "dosage": "500mg BD",
            "rxnorm": "6809",
            "confidence": 0.85,
        }
        result = medication_to_fhir(medication)
        coding = result.get("medicationCodeableConcept", {}).get("coding", [])
        assert len(coding) > 0
        rxnorm_entries = [c for c in coding if "rxnorm" in c.get("system", "").lower()]
        assert len(rxnorm_entries) > 0
        assert rxnorm_entries[0]["code"] == "6809"

    def test_medication_to_fhir_includes_dosage(self):
        medication = {
            "name": "Metformin",
            "dosage": "500mg BD",
            "rxnorm": "6809",
            "confidence": 0.85,
        }
        result = medication_to_fhir(medication)
        dosage_instruction = result.get("dosageInstruction", result.get("dosage", []))
        assert isinstance(dosage_instruction, list)
        assert len(dosage_instruction) > 0


class TestLabToFHIR:

    def test_lab_to_fhir_returns_observation(self):
        lab = {
            "name": "HbA1c",
            "value": 7.8,
            "unit": "%",
            "loinc": "4548-4",
            "ref_low": None,
            "ref_high": 5.6,
        }
        result = lab_to_fhir(lab)
        assert isinstance(result, dict)
        assert result["resourceType"] == "Observation"

    def test_lab_to_fhir_includes_loinc_coding(self):
        lab = {
            "name": "HbA1c",
            "value": 7.8,
            "unit": "%",
            "loinc": "4548-4",
            "ref_low": None,
            "ref_high": 5.6,
        }
        result = lab_to_fhir(lab)
        coding = result.get("code", {}).get("coding", [])
        assert len(coding) > 0
        loinc_entries = [c for c in coding if "loinc" in c.get("system", "").lower()]
        assert len(loinc_entries) > 0
        assert loinc_entries[0]["code"] == "4548-4"

    def test_lab_to_fhir_includes_reference_range(self):
        lab = {
            "name": "Creatinine",
            "value": 1.4,
            "unit": "mg/dL",
            "loinc": "2160-0",
            "ref_low": 0.7,
            "ref_high": 1.3,
        }
        result = lab_to_fhir(lab)
        ref_range = result.get("referenceRange", [])
        assert isinstance(ref_range, list)
        assert len(ref_range) > 0
        first_range = ref_range[0]
        assert "low" in first_range or "high" in first_range
