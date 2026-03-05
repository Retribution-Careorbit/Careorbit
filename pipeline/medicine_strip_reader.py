import re
from utils.drug_database import DrugDatabase


class MedicineStripReader:
    def __init__(self):
        self._drug_db = DrugDatabase()

    def extract(self, text: str) -> dict:
        brand_name = self._extract_brand_name(text)
        manufacturer = self._extract_manufacturer(text)
        expiry = self._extract_expiry(text)
        generic_name = self._extract_generic_name(text, brand_name)

        return {
            "brand_name": brand_name,
            "manufacturer": manufacturer,
            "expiry": expiry,
            "generic_name": generic_name,
        }

    def _extract_brand_name(self, text: str) -> str:
        lines = text.strip().split("\n")
        if lines:
            first_line = lines[0].strip()
            return first_line
        return ""

    def _extract_manufacturer(self, text: str) -> str:
        patterns = [
            re.compile(r'(?:Mfg\.?\s*(?:by)?|Manufactured\s*by)\s*[:\s]*(.+)', re.IGNORECASE),
            re.compile(r'(.+?(?:Pvt|Private|Ltd|Limited|Inc|Corp|Pharma|Labs?|Laboratories).+)', re.IGNORECASE),
        ]
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                mfg = match.group(1).strip()
                mfg = re.sub(r'\s*(Exp|Batch|Mfg).*$', '', mfg, flags=re.IGNORECASE).strip()
                if len(mfg) > 3:
                    return mfg
        return ""

    def _extract_expiry(self, text: str) -> str:
        patterns = [
            re.compile(r'Exp(?:iry)?[:\s]*(\d{1,2}/\d{4})', re.IGNORECASE),
            re.compile(r'Exp(?:iry)?[:\s]*(\d{1,2}-\d{4})', re.IGNORECASE),
            re.compile(r'Exp(?:iry)?[:\s]*([A-Za-z]+\s*\d{4})', re.IGNORECASE),
        ]
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_generic_name(self, text: str, brand_name: str) -> str:
        generic_pattern = re.compile(
            r'([A-Za-z]+(?:\s+[A-Za-z]+)*)\s+(?:IP|BP|USP|Hydrochloride|HCl|Tablets?|Capsules?)',
            re.IGNORECASE
        )
        match = generic_pattern.search(text)
        if match:
            candidate = match.group(1).strip()
            candidate_clean = re.sub(r'\s+(Hydrochloride|HCl|Sodium|Potassium|Maleate|Succinate|Besylate|Fumarate)$', '', candidate, flags=re.IGNORECASE).strip()
            drug_match = self._drug_db.fuzzy_match(candidate_clean)
            if drug_match.confidence >= 0.5:
                return drug_match.generic_name

        brand_base = re.sub(r'[-\s]\w*\d+.*$', '', brand_name).strip()
        drug_match = self._drug_db.fuzzy_match(brand_base)
        if drug_match.confidence >= 0.5:
            return drug_match.generic_name

        return brand_name
