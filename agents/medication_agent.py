from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from agents.contracts import InteractionResult


_SEVERITY_ORDER = {
    "low": 0,
    "moderate": 1,
    "elevated": 2,
    "high": 3,
    "critical": 4,
    "contraindicated": 5,
}


class MedicationAgent(BaseAgent):
    """Detect medication interactions via exact RxNorm retrieval and PHIG lab-aware escalation."""

    def __init__(self, patient_id: str, requesting_user_id: str, search_client, db_factory=None):
        super().__init__(patient_id=patient_id, requesting_user_id=requesting_user_id, db_factory=db_factory)
        self.search_client = search_client

    @staticmethod
    def _normalize_severity(value: str | None) -> str:
        text = str(value or "moderate").strip().lower()
        if text not in _SEVERITY_ORDER:
            return "moderate"
        return text

    @staticmethod
    def _severity_label(value: str) -> str:
        text = MedicationAgent._normalize_severity(value)
        return text.upper()

    @staticmethod
    def _escalate(base_severity: str, egfr: float | None, creatinine: float | None, age: int | None) -> tuple[str, list[str]]:
        sev = MedicationAgent._normalize_severity(base_severity)
        reasons: list[str] = []

        steps = 0
        if egfr is not None and float(egfr) < 60:
            steps += 1
            reasons.append(f"eGFR {egfr} indicates renal impairment")
        if creatinine is not None and float(creatinine) > 1.3:
            steps += 1
            reasons.append(f"Creatinine {creatinine} above normal range")
        if age is not None and int(age) > 70:
            steps += 1
            reasons.append(f"Age {age} increases adverse event risk")

        for _ in range(steps):
            if sev == "contraindicated":
                break
            idx = _SEVERITY_ORDER.get(sev, 1)
            next_idx = min(idx + 1, max(_SEVERITY_ORDER.values()))
            sev = next(k for k, v in _SEVERITY_ORDER.items() if v == next_idx)

        return sev, reasons

    @staticmethod
    def _extract_lab_context(labs: list[dict[str, Any]]) -> tuple[float | None, float | None]:
        egfr = None
        creatinine = None
        for lab in labs:
            name = str(lab.get("name") or "").strip().lower()
            value = lab.get("value")
            try:
                val = float(value) if value is not None else None
            except (TypeError, ValueError):
                val = None
            if val is None:
                continue
            if name == "egfr":
                egfr = val
            if name == "creatinine":
                creatinine = val
        return egfr, creatinine

    async def _get_patient_age(self) -> int | None:
        async with self._db_factory() as session:
            res = await session.execute(
                "SELECT date_of_birth FROM users WHERE id = :pid",
                {"pid": self.patient_id},
            )
            row = res.mappings().first()
            dob = (row or {}).get("date_of_birth")
            if not dob:
                return None
            from datetime import date

            today = date.today()
            return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    async def run(self) -> list[InteractionResult]:
        medications = await self.get_medications()
        if len(medications) < 2:
            return []

        labs = await self.get_lab_results()
        egfr, creatinine = self._extract_lab_context(labs)
        age = await self._get_patient_age()

        results: list[InteractionResult] = []

        for i, med1 in enumerate(medications):
            for med2 in medications[i + 1 :]:
                rx1 = str(med1.get("rxnorm_code") or "").strip()
                rx2 = str(med2.get("rxnorm_code") or "").strip()
                if not rx1 or not rx2:
                    continue

                interaction = await self.search_client.find_interaction_exact(rx1, rx2)
                if not interaction:
                    continue

                validation = self.search_client.validator.validate_interaction(
                    query_rxnorm1=rx1,
                    query_rxnorm2=rx2,
                    result=interaction,
                )
                if not validation.valid:
                    continue

                base_severity = self._normalize_severity(interaction.get("severity"))
                escalated_severity, reasons = self._escalate(base_severity, egfr=egfr, creatinine=creatinine, age=age)

                await self.write_edge(
                    source_id=med1.get("id") or "",
                    target_id=med2.get("id") or "",
                    edge_type="interaction",
                    severity=self._severity_label(escalated_severity),
                    description=str(interaction.get("description") or ""),
                    clinical_action=str(interaction.get("recommendation") or interaction.get("clinical_action") or ""),
                    metadata={
                        "semantic_edge_type": "INTERACTS_WITH",
                        "base_severity": self._severity_label(base_severity),
                        "escalated_severity": self._severity_label(escalated_severity),
                        "escalation_reasons": reasons,
                        "source": interaction.get("source") or "curated_rag",
                        "drug_pair": f"{med1.get('name', '')} + {med2.get('name', '')}",
                        "rxnorm_pair": [rx1, rx2],
                        "lab_modifiers": {
                            "egfr": egfr,
                            "creatinine": creatinine,
                            "age": age,
                        },
                    },
                )

                results.append(
                    InteractionResult(
                        drug1_name=str(med1.get("name") or ""),
                        drug2_name=str(med2.get("name") or ""),
                        base_severity=self._severity_label(base_severity),
                        escalated_severity=self._severity_label(escalated_severity),
                        source=str(interaction.get("source") or "curated_rag"),
                        description=str(interaction.get("description") or ""),
                        recommendation=str(interaction.get("recommendation") or interaction.get("clinical_action") or ""),
                        metadata={
                            "escalation_reasons": reasons,
                            "rxnorm_pair": [rx1, rx2],
                        },
                    )
                )

        return results
