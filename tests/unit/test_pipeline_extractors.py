# tests/unit/test_pipeline_extractors.py
# TDD RED tests for pipeline extractors:
#   pipeline/document_classifier.py
#   pipeline/prescription_extractor.py
#   pipeline/lab_report_extractor.py
#   pipeline/medicine_strip_reader.py

import pytest
from unittest.mock import patch, MagicMock

from pipeline.document_classifier import DocumentClassifier
from pipeline.prescription_extractor import PrescriptionExtractor
from pipeline.lab_report_extractor import LabReportExtractor
from pipeline.medicine_strip_reader import MedicineStripReader


@pytest.fixture
def classifier():
    return DocumentClassifier()


@pytest.fixture
def prescription_extractor():
    return PrescriptionExtractor()


@pytest.fixture
def lab_extractor():
    return LabReportExtractor()


@pytest.fixture
def strip_reader():
    return MedicineStripReader()


class TestDocumentClassifier:

    def test_classifier_prescription_keywords(self, classifier):
        result = classifier.classify("Rx Tab Metformin 500mg BD")
        assert result == "prescription"

    def test_classifier_lab_report_keywords(self, classifier):
        result = classifier.classify("HbA1c 7.2% mg/dl pathology")
        assert result == "lab_report"

    def test_classifier_medicine_strip(self, classifier):
        result = classifier.classify("Mfg Cipla Pvt Ltd Batch B123 Exp 2025")
        assert result == "medicine_strip"

    def test_classifier_unknown_document(self, classifier):
        result = classifier.classify("Hello world random text")
        assert result == "unknown"


class TestPrescriptionExtractor:

    def test_prescription_extractor_returns_medications(self, prescription_extractor):
        ocr_text = (
            "Dr. Amit Roy\nRx:\n"
            "1. Tab Metformin 500mg - 1 BD\n"
            "2. Tab Amlodipine 5mg - 1 OD"
        )
        result = prescription_extractor.extract(ocr_text)
        assert isinstance(result, list)
        assert len(result) > 0
        for med in result:
            assert "name" in med
            assert "dosage" in med
            assert "frequency" in med

    def test_prescription_extractor_maps_indian_brands(self, prescription_extractor):
        ocr_text = "Rx:\n1. Tab Glycomet 500mg - 1 BD"
        result = prescription_extractor.extract(ocr_text)
        generic_names = [med["name"].lower() for med in result]
        assert any("metformin" in name for name in generic_names), (
            f"Expected Glycomet mapped to Metformin, got names: {generic_names}"
        )

    def test_prescription_extractor_parses_frequency_codes(self, prescription_extractor):
        ocr_text = "Rx:\n1. Tab Metformin 500mg BD\n2. Tab Amlodipine 5mg OD"
        result = prescription_extractor.extract(ocr_text)
        frequencies = [med["frequency"].lower() for med in result]
        assert any("twice daily" in f for f in frequencies), (
            f"Expected BD -> 'twice daily', got frequencies: {frequencies}"
        )
        assert any("once daily" in f for f in frequencies), (
            f"Expected OD -> 'once daily', got frequencies: {frequencies}"
        )


class TestLabReportExtractor:

    def test_lab_extractor_returns_test_results(self, lab_extractor):
        ocr_text = (
            "PATHCARE LABS\n"
            "HbA1c: 7.8% (Ref: <5.7%)\n"
            "Creatinine: 1.4 mg/dL (Ref: 0.7-1.3)"
        )
        result = lab_extractor.extract(ocr_text)
        assert isinstance(result, list)
        assert len(result) > 0
        for test_result in result:
            assert "name" in test_result
            assert "value" in test_result
            assert "unit" in test_result
            assert "reference_range" in test_result

    def test_lab_extractor_flags_abnormal_values(self, lab_extractor):
        ocr_text = "Creatinine: 1.4 mg/dL (Ref: 0.7-1.3)"
        result = lab_extractor.extract(ocr_text)
        assert len(result) > 0
        creatinine = next(
            (t for t in result if "creatinine" in t["name"].lower()), None
        )
        assert creatinine is not None, "Creatinine test not found in results"
        assert creatinine["is_abnormal"] is True

    def test_lab_extractor_assigns_loinc_codes(self, lab_extractor):
        ocr_text = "HbA1c: 7.8% (Ref: <5.7%)"
        result = lab_extractor.extract(ocr_text)
        assert len(result) > 0
        hba1c = next(
            (t for t in result if "hba1c" in t["name"].lower()), None
        )
        assert hba1c is not None, "HbA1c test not found in results"
        assert "loinc_code" in hba1c
        assert hba1c["loinc_code"] == "4548-4"


class TestMedicineStripReader:

    def test_strip_reader_extracts_drug_info(self, strip_reader):
        ocr_text = (
            "GLYCOMET-GP 2\nMetformin Hydrochloride IP 500mg\n"
            "USV Private Limited\n"
            "Mfg: 06/2025  Exp: 05/2027\nBatch: GG2345"
        )
        result = strip_reader.extract(ocr_text)
        assert isinstance(result, dict)
        assert "brand_name" in result
        assert "manufacturer" in result
        assert "expiry" in result

    def test_strip_reader_maps_brand_to_generic(self, strip_reader):
        ocr_text = (
            "GLYCOMET-GP 2\nMetformin Hydrochloride IP 500mg\n"
            "USV Private Limited\n"
            "Mfg: 06/2025  Exp: 05/2027\nBatch: GG2345"
        )
        result = strip_reader.extract(ocr_text)
        assert "generic_name" in result
        assert "metformin" in result["generic_name"].lower(), (
            f"Expected brand mapped to generic via DrugDatabase, got: {result['generic_name']}"
        )
