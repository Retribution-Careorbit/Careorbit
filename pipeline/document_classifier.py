import re


class DocumentClassifier:
    PRESCRIPTION_KEYWORDS = ["rx", "tab", "cap", "syrup", "inject", "prescription", "dosage", "mg", "mcg"]
    LAB_REPORT_KEYWORDS = ["pathology", "laboratory", "hba1c", "creatinine", "hemoglobin", "cholesterol",
                           "mg/dl", "g/dl", "ref:", "reference", "lab report", "blood test", "urine test"]
    MEDICINE_STRIP_KEYWORDS = ["mfg", "exp", "batch", "pvt ltd", "private limited", "manufactured",
                               "expiry", "manufacturing"]

    def classify(self, text: str) -> str:
        lower = text.lower()

        strip_score = sum(1 for kw in self.MEDICINE_STRIP_KEYWORDS if kw in lower)
        if strip_score >= 2:
            return "medicine_strip"

        lab_score = sum(1 for kw in self.LAB_REPORT_KEYWORDS if kw in lower)
        if lab_score >= 2:
            return "lab_report"

        rx_score = sum(1 for kw in self.PRESCRIPTION_KEYWORDS if kw in lower)
        if rx_score >= 2:
            return "prescription"

        return "unknown"
