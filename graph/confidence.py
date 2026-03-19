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
        "prescription_digital": 0.95,
        "lab_report_photo": 0.88,
        "lab_report_digital": 0.98,
        "medicine_strip_photo": 0.90,
        "patient_text_input": 0.60,
        "voice_input": 0.50,
        "patient_confirmed": 0.85,
        "patient_corrected": 0.85,
    }

    BYPASS_SOURCES = {"patient_confirmed", "patient_corrected"}

    @classmethod
    def _get_label(cls, score: float) -> str:
        if score >= 0.80:
            return "VERIFIED"
        elif score >= 0.65:
            return "HIGH"
        elif score >= 0.40:
            return "MODERATE"
        else:
            return "LOW"

    @classmethod
    def compute_node_confidence(
        cls,
        source_type: str,
        ocr_confidence: float,
        ner_match: bool,
        patient_verified: bool,
    ) -> float:
        """
        Deterministic confidence formula.
        Same inputs always produce the same confidence score.
        """
        ceiling = cls.SOURCE_CEILINGS.get(source_type, 0.50)
        ocr_factor = min(max(float(ocr_confidence), 0.0), 1.0)
        ner_factor = 1.0 if ner_match else 0.7
        verification_factor = 1.0 if patient_verified else 0.85
        raw = ocr_factor * ner_factor * verification_factor
        final = min(raw, ceiling)
        return round(final, 2)

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
        ner_match = bool(drug_match_score >= 0.5)
        final_score = cls.compute_node_confidence(
            source_type=source_type,
            ocr_confidence=ocr_avg_confidence,
            ner_match=ner_match,
            patient_verified=patient_confirmed,
        )

        return ConfidenceBreakdown(
            final_score=final_score,
            confidence_label=cls._get_label(final_score),
            breakdown={
                "source_type": source_type,
                "ocr_confidence": round(float(ocr_avg_confidence or 0.0), 4),
                "ner_match": ner_match,
                "patient_verified": bool(patient_confirmed),
                "dosage_parsed": bool(dosage_parsed),
                "date_found": bool(date_found),
            },
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
        ner_match = bool(value_parsed and unit_recognized)
        final_score = cls.compute_node_confidence(
            source_type=source_type,
            ocr_confidence=ocr_avg_confidence,
            ner_match=ner_match,
            patient_verified=patient_confirmed,
        )

        return ConfidenceBreakdown(
            final_score=final_score,
            confidence_label=cls._get_label(final_score),
            breakdown={
                "source_type": source_type,
                "ocr_confidence": round(float(ocr_avg_confidence or 0.0), 4),
                "ner_match": ner_match,
                "patient_verified": bool(patient_confirmed),
                "reference_range_found": bool(reference_range_found),
            },
        )
