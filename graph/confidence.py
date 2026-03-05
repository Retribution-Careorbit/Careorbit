from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ConfidenceBreakdown:
    final_score: float
    confidence_label: str
    breakdown: Optional[dict] = field(default_factory=dict)


class ConfidenceCalculator:
    SOURCE_CEILINGS = {
        "prescription_photo": 0.85,
        "lab_report_photo": 0.88,
        "medicine_strip_photo": 0.90,
        "patient_text_input": 0.60,
        "patient_confirmed": 0.85,
        "patient_corrected": 0.85,
    }

    BYPASS_SOURCES = {"patient_confirmed", "patient_corrected"}

    @classmethod
    def _get_label(cls, score: float) -> str:
        if score >= 0.80:
            return "VERIFIED"
        elif score >= 0.60:
            return "HIGH"
        elif score >= 0.40:
            return "MODERATE"
        else:
            return "LOW"

    @classmethod
    def calculate_medication_confidence(
        cls,
        source_type: str,
        ocr_avg_confidence: float,
        drug_match_score: float,
        dosage_parsed: bool,
        date_found: bool,
        patient_confirmed: bool,
    ) -> ConfidenceBreakdown:
        if source_type in cls.BYPASS_SOURCES:
            return ConfidenceBreakdown(
                final_score=0.85,
                confidence_label="VERIFIED",
                breakdown={},
            )

        ceiling = cls.SOURCE_CEILINGS.get(source_type, 0.60)

        weights = {
            "ocr": 0.30,
            "drug_match": 0.35,
            "dosage": 0.15,
            "date": 0.10,
            "confirmation": 0.10,
        }

        components = {
            "ocr": ocr_avg_confidence * weights["ocr"],
            "drug_match": drug_match_score * weights["drug_match"],
            "dosage": (1.0 if dosage_parsed else 0.0) * weights["dosage"],
            "date": (1.0 if date_found else 0.0) * weights["date"],
            "confirmation": (1.0 if patient_confirmed else 0.0) * weights["confirmation"],
        }

        raw_score = sum(components.values())
        final_score = max(0.0, min(raw_score, ceiling))

        return ConfidenceBreakdown(
            final_score=round(final_score, 4),
            confidence_label=cls._get_label(final_score),
            breakdown=components,
        )

    @classmethod
    def calculate_lab_confidence(
        cls,
        source_type: str,
        ocr_avg_confidence: float,
        value_parsed: bool,
        unit_recognized: bool,
        reference_range_found: bool,
        patient_confirmed: bool,
    ) -> ConfidenceBreakdown:
        if source_type in cls.BYPASS_SOURCES:
            return ConfidenceBreakdown(
                final_score=0.85,
                confidence_label="VERIFIED",
                breakdown={},
            )

        ceiling = cls.SOURCE_CEILINGS.get(source_type, 0.60)

        weights = {
            "ocr": 0.30,
            "value_parsed": 0.25,
            "unit": 0.20,
            "reference": 0.15,
            "confirmation": 0.10,
        }

        components = {
            "ocr": ocr_avg_confidence * weights["ocr"],
            "value_parsed": (1.0 if value_parsed else 0.0) * weights["value_parsed"],
            "unit": (1.0 if unit_recognized else 0.0) * weights["unit"],
            "reference": (1.0 if reference_range_found else 0.0) * weights["reference"],
            "confirmation": (1.0 if patient_confirmed else 0.0) * weights["confirmation"],
        }

        raw_score = sum(components.values())
        final_score = max(0.0, min(raw_score, ceiling))

        return ConfidenceBreakdown(
            final_score=round(final_score, 4),
            confidence_label=cls._get_label(final_score),
            breakdown=components,
        )
