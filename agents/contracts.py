from typing import Optional

from pydantic import BaseModel, Field, field_validator


ALLOWED_SEVERITIES = {"LOW", "MODERATE", "ELEVATED", "HIGH", "CONTRAINDICATED", "UNKNOWN"}
ALLOWED_CARE_GAP_STATUS = {"open", "resolved", "closed", "completed"}


class InteractionAlertContract(BaseModel):
    drug_pair: str = Field(min_length=3)
    severity: str = Field(default="UNKNOWN")
    description: str = Field(min_length=3)
    clinical_action: str = Field(default="Review with physician")
    acknowledged: bool = False

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        normalized = str(value or "UNKNOWN").strip().upper()
        if normalized not in ALLOWED_SEVERITIES:
            raise ValueError(f"Unsupported severity: {value}")
        return normalized


class CareGapContract(BaseModel):
    name: str = Field(min_length=3)
    status: str = Field(default="open")
    condition_code: Optional[str] = None
    guideline_source: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = str(value or "open").strip().lower()
        if normalized not in ALLOWED_CARE_GAP_STATUS:
            raise ValueError(f"Unsupported care gap status: {value}")
        return normalized
