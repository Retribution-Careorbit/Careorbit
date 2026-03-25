from __future__ import annotations

import re
import math
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from db.session import async_session


DOSAGE_PATTERN = re.compile(
    r"(?ix)^(?:\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|iu)|\d+\s*(?:tablet|tab|capsule|cap|drop|puff)s?)$"
)

FREQUENCY_WHITELIST = {
    "",
    "od",
    "bd",
    "tds",
    "qid",
    "qhs",
    "q4h",
    "q6h",
    "q8h",
    "daily",
    "once daily",
    "twice daily",
    "three times daily",
    "weekly",
    "monthly",
    "am",
    "pm",
    "prn",
    "sos",
    "stat",
    "bid",
    "tid",
}

LAB_RULES = {
    "hba1c": {
        "loinc": "4548-4",
        "units": {"%"},
        "plausible_min": 2.0,
        "plausible_max": 20.0,
    },
    "creatinine": {
        "loinc": "2160-0",
        "units": {"mg/dl", "mg/dL"},
        "plausible_min": 0.1,
        "plausible_max": 20.0,
    },
    "egfr": {
        "loinc": "33914-3",
        "units": {"ml/min", "mL/min", "ml/min/1.73m2", "mL/min/1.73m2"},
        "plausible_min": 1.0,
        "plausible_max": 200.0,
    },
    "tsh": {
        "loinc": "3016-3",
        "units": {"uiu/ml", "uIU/mL", "miu/l", "mIU/L"},
        "plausible_min": 0.01,
        "plausible_max": 150.0,
    },
    "alt": {
        "loinc": "1742-6",
        "units": {"u/l", "U/L"},
        "plausible_min": 1.0,
        "plausible_max": 2000.0,
    },
}


@dataclass
class GateDecision:
    accepted: bool
    reasons: list[str]
    agreement_count: int


def _normalize_uuid(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError):
        return None


class ValidationGate:
    async def validate_medication(
        self,
        patient_id: str,
        medication: dict[str, Any],
        user_confirmed_names: set[str],
        ner_names: set[str],
    ) -> GateDecision:
        name = str(medication.get("name") or "").strip()
        dosage = str(medication.get("dosage") or "").strip()
        frequency = str(medication.get("frequency") or "").strip().lower()

        reasons: list[str] = []
        if not name:
            reasons.append("missing_name")
            return GateDecision(accepted=False, reasons=reasons, agreement_count=0)

        agreement_count = 1  # GPT/orchestrator is one source by construction.
        if name.lower() in user_confirmed_names:
            agreement_count += 1
        if name.lower() in ner_names:
            agreement_count += 1

        if agreement_count < 2:
            reasons.append("insufficient_source_agreement")

        if not dosage or not DOSAGE_PATTERN.match(dosage):
            reasons.append("invalid_dosage_format")

        if frequency not in FREQUENCY_WHITELIST:
            reasons.append("unsupported_frequency")

        duplicate = await self._is_recent_duplicate(patient_id=patient_id, medication_name=name)
        if duplicate:
            reasons.append("duplicate_recent_medication")

        return GateDecision(accepted=not reasons, reasons=reasons, agreement_count=agreement_count)

    async def _is_recent_duplicate(self, patient_id: str, medication_name: str) -> bool:
        normalized_patient_id = _normalize_uuid(patient_id)
        if not normalized_patient_id:
            return False

        try:
            async with async_session() as session:
                duplicate_result = await session.execute(
                    "SELECT id FROM phig_nodes "
                    "WHERE patient_id = :pid "
                    "AND node_type = CAST('medication' AS node_type) "
                    "AND is_active = TRUE "
                    "AND LOWER(display_name) = :med_name "
                    "AND updated_at >= NOW() - INTERVAL '30 days' "
                    "LIMIT 1",
                    {
                        "pid": normalized_patient_id,
                        "med_name": medication_name.lower(),
                    },
                )
                return duplicate_result.mappings().first() is not None
        except Exception:
            return False

    async def validate_lab_result(
        self,
        patient_id: str,
        lab_result: dict[str, Any],
        ner_names: set[str],
        text_anchor_names: set[str],
    ) -> GateDecision:
        name = str(lab_result.get("name") or "").strip()
        unit = str(lab_result.get("unit") or "").strip()
        loinc = str(lab_result.get("loinc") or "").strip()

        reasons: list[str] = []
        if not name:
            reasons.append("missing_lab_name")
            return GateDecision(accepted=False, reasons=reasons, agreement_count=0)

        name_key = name.lower()
        agreement_count = 1  # Extracted result source.
        if name_key in ner_names:
            agreement_count += 1
        if name_key in text_anchor_names:
            agreement_count += 1
        if agreement_count < 2:
            reasons.append("insufficient_source_agreement")

        try:
            value = float(lab_result.get("value"))
            if not math.isfinite(value):
                raise ValueError("non-finite")
        except (TypeError, ValueError):
            reasons.append("invalid_lab_value")
            return GateDecision(accepted=False, reasons=reasons, agreement_count=agreement_count)

        rule = LAB_RULES.get(name_key)
        if rule:
            if loinc and str(rule.get("loinc") or "").lower() != loinc.lower():
                reasons.append("loinc_mismatch")

            allowed_units = {str(u).lower() for u in (rule.get("units") or set())}
            if unit and unit.lower() not in allowed_units:
                reasons.append("unsupported_lab_unit")

            plausible_min = float(rule.get("plausible_min"))
            plausible_max = float(rule.get("plausible_max"))
            if value < plausible_min or value > plausible_max:
                reasons.append("implausible_lab_value")

        duplicate = await self._is_recent_duplicate_lab(patient_id=patient_id, lab_name=name, value=value)
        if duplicate:
            reasons.append("duplicate_recent_lab")

        return GateDecision(accepted=not reasons, reasons=reasons, agreement_count=agreement_count)

    async def _is_recent_duplicate_lab(self, patient_id: str, lab_name: str, value: float) -> bool:
        normalized_patient_id = _normalize_uuid(patient_id)
        if not normalized_patient_id:
            return False

        try:
            async with async_session() as session:
                duplicate_result = await session.execute(
                    "SELECT id FROM phig_nodes "
                    "WHERE patient_id = :pid "
                    "AND node_type = CAST('lab_result' AS node_type) "
                    "AND is_active = TRUE "
                    "AND LOWER(display_name) = :lab_name "
                    "AND value = :lab_value "
                    "AND updated_at >= NOW() - INTERVAL '30 days' "
                    "LIMIT 1",
                    {
                        "pid": normalized_patient_id,
                        "lab_name": lab_name.lower(),
                        "lab_value": float(value),
                    },
                )
                return duplicate_result.mappings().first() is not None
        except Exception:
            return False


validation_gate = ValidationGate()
