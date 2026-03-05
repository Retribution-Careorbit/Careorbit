# tests/unit/test_drug_database.py
# V3 FIX Q7: Losartan RxNorm 52175 → 202272 (ingredient-level)

import pytest
from utils.drug_database import DrugDatabase, DrugMatchResult


@pytest.fixture
def drug_db():
    return DrugDatabase()


class TestRxNormCodes:
    """Validate RxNorm codes for commonly prescribed Indian medications."""

    KNOWN_CODES = {
        "Metformin": "6809",
        "Amlodipine": "17767",
        "Atorvastatin": "83367",
        "Aspirin": "1191",
        "Ibuprofen": "5640",
        "Telmisartan": "73494",
        "Levothyroxine": "10582",
        "Losartan": "202272",        # V3 FIX Q7: ingredient-level, not 52175
        "Omeprazole": "7646",
        "Paracetamol": "161",
    }

    @pytest.mark.parametrize("drug,code", KNOWN_CODES.items())
    def test_rxnorm_codes_correct(self, drug_db, drug, code):
        result = drug_db.fuzzy_match(drug)
        assert result.rxnorm_code == code, \
            f"{drug}: expected RxNorm {code}, got {result.rxnorm_code}"


class TestFuzzyMatching:

    def test_exact_match_returns_high_confidence(self, drug_db):
        result = drug_db.fuzzy_match("Metformin")
        assert result.confidence >= 0.95
        assert result.generic_name.lower() == "metformin"

    def test_case_insensitive_match(self, drug_db):
        lower = drug_db.fuzzy_match("metformin")
        upper = drug_db.fuzzy_match("METFORMIN")
        assert lower.rxnorm_code == upper.rxnorm_code

    def test_typo_tolerance(self, drug_db):
        """Common OCR errors: 'Meformin', 'Amlodlpine'."""
        result = drug_db.fuzzy_match("Meformin")
        assert result.rxnorm_code == "6809"  # Should match Metformin

    def test_indian_brand_to_generic(self, drug_db):
        """Glycomet → Metformin."""
        result = drug_db.fuzzy_match("Glycomet")
        assert result.generic_name.lower() == "metformin"

    def test_unknown_drug_returns_low_confidence(self, drug_db):
        result = drug_db.fuzzy_match("Xyzdrugthatdoesnotexist")
        assert result.confidence < 0.5

    def test_none_input_returns_zero_confidence(self, drug_db):
        """Contract: None → DrugMatchResult(confidence=0.0)."""
        result = drug_db.fuzzy_match(None)
        assert isinstance(result, DrugMatchResult)
        assert result.confidence == 0.0

    def test_empty_string_returns_zero_confidence(self, drug_db):
        result = drug_db.fuzzy_match("")
        assert result.confidence == 0.0

    def test_dosage_disambiguation(self, drug_db):
        """'Atorvastatin 10mg' and 'Atorvastatin 40mg' both → same drug."""
        r1 = drug_db.fuzzy_match("Atorvastatin 10mg")
        r2 = drug_db.fuzzy_match("Atorvastatin 40mg")
        assert r1.rxnorm_code == r2.rxnorm_code == "83367"
