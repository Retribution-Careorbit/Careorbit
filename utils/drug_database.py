from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DrugMatchResult:
    rxnorm_code: str = ""
    generic_name: str = ""
    confidence: float = 0.0
    brand_names: list = field(default_factory=list)


class DrugDatabase:
    DRUGS = {
        "metformin": {"rxnorm": "6809", "brands": ["Glycomet", "Glucophage", "Obimet", "Glyciphage"]},
        "amlodipine": {"rxnorm": "17767", "brands": ["Amlong", "Amlip", "Stamlo"]},
        "atorvastatin": {"rxnorm": "83367", "brands": ["Atorva", "Lipitor", "Tonact"]},
        "aspirin": {"rxnorm": "1191", "brands": ["Ecosprin", "Disprin", "Aspro"]},
        "ibuprofen": {"rxnorm": "5640", "brands": ["Brufen", "Ibugesic", "Combiflam"]},
        "telmisartan": {"rxnorm": "73494", "brands": ["Telma", "Telmikind", "Telsar"]},
        "levothyroxine": {"rxnorm": "10582", "brands": ["Thyronorm", "Eltroxin", "Lethyrox"]},
        "losartan": {"rxnorm": "202272", "brands": ["Losacar", "Repace", "Losar"]},
        "omeprazole": {"rxnorm": "7646", "brands": ["Omez", "Ocid", "Omesec"]},
        "paracetamol": {"rxnorm": "161", "brands": ["Crocin", "Dolo", "Calpol", "Metacin"]},
    }

    BRAND_TO_GENERIC = {}

    def __init__(self):
        for generic, info in self.DRUGS.items():
            for brand in info["brands"]:
                self.BRAND_TO_GENERIC[brand.lower()] = generic

    def _strip_dosage(self, name: str) -> str:
        import re
        return re.sub(r'\s*\d+\s*(mg|mcg|g|ml|iu)\b.*$', '', name, flags=re.IGNORECASE).strip()

    def _levenshtein(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        return prev_row[-1]

    def fuzzy_match(self, drug_name) -> DrugMatchResult:
        if drug_name is None or drug_name == "":
            return DrugMatchResult(confidence=0.0)

        cleaned = self._strip_dosage(drug_name)
        lower = cleaned.lower()

        if lower in self.DRUGS:
            info = self.DRUGS[lower]
            return DrugMatchResult(
                rxnorm_code=info["rxnorm"],
                generic_name=lower.capitalize(),
                confidence=1.0,
                brand_names=info["brands"],
            )

        if lower in self.BRAND_TO_GENERIC:
            generic = self.BRAND_TO_GENERIC[lower]
            info = self.DRUGS[generic]
            return DrugMatchResult(
                rxnorm_code=info["rxnorm"],
                generic_name=generic.capitalize(),
                confidence=0.95,
                brand_names=info["brands"],
            )

        best_match = None
        best_distance = float("inf")
        for generic in self.DRUGS:
            dist = self._levenshtein(lower, generic)
            if dist < best_distance:
                best_distance = dist
                best_match = generic

        if best_match and best_distance <= 2:
            info = self.DRUGS[best_match]
            confidence = max(0.5, 1.0 - (best_distance * 0.15))
            return DrugMatchResult(
                rxnorm_code=info["rxnorm"],
                generic_name=best_match.capitalize(),
                confidence=confidence,
                brand_names=info["brands"],
            )

        if best_match and best_distance <= 4:
            info = self.DRUGS[best_match]
            confidence = max(0.3, 1.0 - (best_distance * 0.2))
            return DrugMatchResult(
                rxnorm_code=info["rxnorm"],
                generic_name=best_match.capitalize(),
                confidence=confidence,
                brand_names=info["brands"],
            )

        return DrugMatchResult(
            rxnorm_code="",
            generic_name=cleaned,
            confidence=0.1,
            brand_names=[],
        )
