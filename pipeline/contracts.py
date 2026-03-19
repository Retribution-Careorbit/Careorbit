from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MedicationExtraction(BaseModel):
    name: str = Field(min_length=2)
    dosage: str = ""
    frequency: str = ""
    rxnorm: Optional[str] = None
    condition_code: Optional[str] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 2:
            raise ValueError("Medication name is too short")
        return normalized

    @field_validator("condition_code")
    @classmethod
    def normalize_condition_code(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return str(value).strip().upper()


class LabExtraction(BaseModel):
    name: str = Field(min_length=2)
    value: float
    unit: str = ""
    ref_low: Optional[float] = None
    ref_high: Optional[float] = None
    loinc: Optional[str] = None
    condition_code: Optional[str] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 2:
            raise ValueError("Lab marker name is too short")
        return normalized

    @field_validator("condition_code")
    @classmethod
    def normalize_condition_code(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return str(value).strip().upper()


class ConditionExtraction(BaseModel):
    name: str = Field(min_length=2)
    code: Optional[str] = None
    confidence: float = 0.8
    verified: bool = False

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return str(value).strip().upper()

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(str(value or "").split()).strip()
        if len(normalized) < 2:
            raise ValueError("Condition name is too short")
        return normalized


def validate_extraction_payload(payload: dict) -> dict:
    meds = []
    for item in payload.get("medications") or []:
        if not isinstance(item, dict):
            continue
        try:
            meds.append(MedicationExtraction.model_validate(item).model_dump())
        except Exception:
            continue

    labs = []
    for item in payload.get("labs") or []:
        if not isinstance(item, dict):
            continue
        try:
            labs.append(LabExtraction.model_validate(item).model_dump())
        except Exception:
            continue

    conditions = []
    for item in payload.get("conditions") or []:
        if not isinstance(item, dict):
            continue
        try:
            conditions.append(ConditionExtraction.model_validate(item).model_dump())
        except Exception:
            continue

    result = dict(payload)
    result["medications"] = meds
    result["labs"] = labs
    result["conditions"] = conditions
    return result
