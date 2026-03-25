import pytest

from graph.phig_integrity import phig_integrity


@pytest.mark.asyncio
async def test_verify_consistency_non_uuid_patient_is_safe_noop():
    result = await phig_integrity.verify_consistency("non-uuid-patient")
    assert result["passed"] is True
    assert result["errors"] == []


@pytest.mark.asyncio
async def test_snapshot_and_rollback_non_uuid_patient_uses_in_memory_path():
    snapshot_id = await phig_integrity.create_snapshot("non-uuid-patient", reason="unit_test")
    assert snapshot_id

    rollback_result = await phig_integrity.rollback_snapshot("non-uuid-patient", snapshot_id)
    assert rollback_result is True


def test_lab_plausibility_helper_accepts_valid_known_lab():
    assert phig_integrity._is_lab_value_unit_plausible(
        name="Creatinine",
        value=1.2,
        unit="mg/dL",
        loinc="2160-0",
    ) is True


def test_lab_plausibility_helper_rejects_unit_or_range_mismatch():
    assert phig_integrity._is_lab_value_unit_plausible(
        name="eGFR",
        value=450,
        unit="mg/dL",
        loinc="33914-3",
    ) is False


def test_lab_plausibility_helper_rejects_loinc_mismatch_for_known_lab():
    assert phig_integrity._is_lab_value_unit_plausible(
        name="TSH",
        value=2.0,
        unit="uIU/mL",
        loinc="9999-9",
    ) is False
