import re


class LabReportExtractor:
    LOINC_MAP = {
        "hba1c": "4548-4",
        "hemoglobin a1c": "4548-4",
        "glycated hemoglobin": "4548-4",
        "creatinine": "2160-0",
        "serum creatinine": "2160-0",
        "fasting glucose": "1558-6",
        "fasting blood sugar": "1558-6",
        "fbs": "1558-6",
        "total cholesterol": "2093-3",
        "cholesterol": "2093-3",
        "hemoglobin": "718-7",
        "hb": "718-7",
        "triglycerides": "2571-8",
        "hdl": "2085-9",
        "ldl": "2089-1",
        "urea": "3094-0",
        "blood urea nitrogen": "3094-0",
        "bun": "3094-0",
        "tsh": "3016-3",
        "t3": "3053-6",
        "t4": "3026-2",
        "albumin": "1751-7",
        "bilirubin": "1975-2",
        "sgpt": "1742-6",
        "alt": "1742-6",
        "sgot": "1920-8",
        "ast": "1920-8",
        "platelets": "777-3",
        "wbc": "6690-2",
        "rbc": "789-8",
    }

    def extract(self, text: str) -> list:
        results = []
        pattern = re.compile(
            r'([A-Za-z][A-Za-z0-9 ]+?)\s*:\s*'
            r'([<>]?\s*[\d.]+)\s*'
            r'(%|mg/dL|mg/dl|g/dL|g/dl|mmol/L|mmol/l|U/L|u/l|mIU/L|ng/dL|ng/dl|µg/dL|IU/mL|cells/mcL|x10\^3/uL|x10\^6/uL|mEq/L)?'
            r'(?:\s*\(?\s*[Rr]ef(?:erence)?[:\s]*([^)\n]+)\)?)?',
            re.IGNORECASE
        )

        for match in pattern.finditer(text):
            name = match.group(1).strip()
            value = match.group(2).strip()
            unit = (match.group(3) or "").strip()
            ref_range = (match.group(4) or "").strip()

            if name.lower() in ("pathcare labs", "lab", "labs", "report", "date", "name", "age", "sex", "dr", "doctor"):
                continue

            loinc_code = self._lookup_loinc(name)
            is_abnormal = self._check_abnormal(value, ref_range)

            results.append({
                "name": name,
                "value": value,
                "unit": unit,
                "reference_range": ref_range,
                "is_abnormal": is_abnormal,
                "loinc_code": loinc_code,
            })

        return results

    def _lookup_loinc(self, name: str) -> str:
        lower = name.lower().strip()
        if lower in self.LOINC_MAP:
            return self.LOINC_MAP[lower]
        for key, code in self.LOINC_MAP.items():
            if key in lower or lower in key:
                return code
        return ""

    def _check_abnormal(self, value_str: str, ref_range: str) -> bool:
        if not ref_range:
            return False

        try:
            clean_val = re.sub(r'[<>]', '', value_str).strip()
            value = float(clean_val)
        except (ValueError, TypeError):
            return False

        less_than = re.match(r'<\s*([\d.]+)', ref_range)
        if less_than:
            upper = float(less_than.group(1))
            return value > upper

        range_match = re.match(r'([\d.]+)\s*[-–]\s*([\d.]+)', ref_range)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            return value < low or value > high

        return False
