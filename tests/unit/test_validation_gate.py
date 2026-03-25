import pytest

from pipeline.validation_gate import validation_gate


@pytest.mark.asyncio
async def test_validation_gate_accepts_supported_confirmed_medication():
    decision = await validation_gate.validate_medication(
        patient_id="non-uuid-patient",
        medication={
            "name": "Metformin",
            "dosage": "500 mg",
            "frequency": "BD",
        },
        user_confirmed_names={"metformin"},
        ner_names={"metformin"},
    )

    assert decision.accepted is True
    assert decision.reasons == []
    assert decision.agreement_count >= 2


@pytest.mark.asyncio
async def test_validation_gate_rejects_unverified_bad_format_medication():
    decision = await validation_gate.validate_medication(
        patient_id="non-uuid-patient",
        medication={
            "name": "UnknownDrugX",
            "dosage": "one spoon",
            "frequency": "whenever",
        },
        user_confirmed_names={"metformin"},
        ner_names={"amlodipine"},
    )

    assert decision.accepted is False
    assert "insufficient_source_agreement" in decision.reasons
    assert "invalid_dosage_format" in decision.reasons
    assert "unsupported_frequency" in decision.reasons


@pytest.mark.asyncio
async def test_validation_gate_accepts_plausible_lab_result():
    decision = await validation_gate.validate_lab_result(
        patient_id="non-uuid-patient",
        lab_result={
            "name": "Creatinine",
            "value": 1.2,
            "unit": "mg/dL",
            "loinc": "2160-0",
        },
        ner_names={"creatinine"},
        text_anchor_names={"creatinine"},
    )

    assert decision.accepted is True
    assert decision.reasons == []
    assert decision.agreement_count >= 2


@pytest.mark.asyncio
async def test_validation_gate_rejects_implausible_or_mismatched_lab_result():
    decision = await validation_gate.validate_lab_result(
        patient_id="non-uuid-patient",
        lab_result={
            "name": "eGFR",
            "value": 500,
            "unit": "mg/dL",
            "loinc": "9999-9",
        },
        ner_names=set(),
        text_anchor_names={"egfr"},
    )

    assert decision.accepted is False
    assert "insufficient_source_agreement" in decision.reasons
    assert "unsupported_lab_unit" in decision.reasons
    assert "loinc_mismatch" in decision.reasons
    assert "implausible_lab_value" in decision.reasons
