import re
from utils.drug_database import DrugDatabase


class PrescriptionExtractor:
    FREQUENCY_MAP = {
        "bd": "twice daily",
        "bid": "twice daily",
        "od": "once daily",
        "qd": "once daily",
        "tid": "three times daily",
        "tds": "three times daily",
        "qid": "four times daily",
        "qds": "four times daily",
        "hs": "at bedtime",
        "sos": "as needed",
        "prn": "as needed",
        "stat": "immediately",
    }

    def __init__(self):
        self._drug_db = DrugDatabase()

    def _map_frequency(self, freq_code: str) -> str:
        return self.FREQUENCY_MAP.get(freq_code.lower().strip(), freq_code)

    def extract(self, text: str) -> list:
        results = []
        pattern = re.compile(
            r'(?:Tab|Cap|Syp|Inj)?\s*([A-Za-z][A-Za-z\-]+(?:\s*[A-Za-z\-]+)*?)\s+'
            r'(\d+\s*(?:mg|mcg|g|ml|iu))'
            r'(?:\s*[-–]\s*\d+)?\s*'
            r'([A-Za-z]+)?',
            re.IGNORECASE
        )

        for match in pattern.finditer(text):
            raw_name = match.group(1).strip()
            raw_name = re.sub(r'^(Tab|Cap|Syp|Inj)\s+', '', raw_name, flags=re.IGNORECASE).strip()
            dosage = match.group(2).strip()
            freq_code = match.group(3) or ""

            drug_match = self._drug_db.fuzzy_match(raw_name)
            if drug_match.confidence >= 0.5:
                name = drug_match.generic_name
            else:
                name = raw_name

            frequency = self._map_frequency(freq_code) if freq_code else "as directed"

            results.append({
                "name": name,
                "dosage": dosage,
                "frequency": frequency,
            })

        return results
