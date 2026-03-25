from datetime import datetime, timezone

WEIGHTS = {
    "completeness": 0.25,
    "avg_confidence": 0.20,
    "interaction_risk": 0.25,
    "care_gap_status": 0.20,
    "adherence_rate": 0.10,
}

CORE_TYPES = {"medication", "condition", "lab_value"}
BONUS_TYPES = {"care_gap", "provider"}
SEVERITY_PENALTIES = {
    "elevated": 25,
    "moderate": 15,
    "low": 5,
}

EXPECTED_NODES_PER_CONDITION = {
    "E11.9": {"medications": 1, "lab_results": 2, "screenings": 1},
    "I10": {"medications": 1, "lab_results": 1, "screenings": 0},
    "I48": {"medications": 1, "lab_results": 1, "screenings": 0},
}

DEFAULT_EXPECTED = {"medications": 1, "lab_results": 1, "screenings": 0}


class OrbitScoreCalculator:
    def __init__(self, phig: dict):
        self.phig = phig
        self._score = None

    def _compute_completeness(self) -> float:
        nodes = self.phig.get("nodes", [])
        conditions = [
            n for n in nodes
            if n.get("type") == "condition"
        ]
        if not conditions:
            return 100.0

        # Backward-compatible fallback: if condition nodes are present but none
        # carry ICD/code metadata, score by core type coverage.
        coded_conditions = [
            c for c in conditions
            if str(c.get("icd10") or c.get("code") or "").strip()
        ]
        if not coded_conditions:
            present_core_types = {
                str(n.get("type") or "").lower()
                for n in nodes
                if str(n.get("type") or "").lower() in CORE_TYPES
            }
            return round((len(present_core_types) / len(CORE_TYPES)) * 100.0, 2)

        total_expected_medications = 0
        total_expected_labs = 0
        total_expected_screenings = 0

        for condition in coded_conditions:
            icd_code = str(condition.get("icd10") or condition.get("code") or "").upper()
            expected = EXPECTED_NODES_PER_CONDITION.get(icd_code, DEFAULT_EXPECTED)
            total_expected_medications += int(expected["medications"])
            total_expected_labs += int(expected["lab_results"])
            total_expected_screenings += int(expected["screenings"])

        present_medications = sum(1 for n in nodes if n.get("type") == "medication")
        present_labs = sum(1 for n in nodes if n.get("type") == "lab_value")

        care_gaps = self.phig.get("care_gaps", [])
        resolved_screenings = sum(
            1
            for g in care_gaps
            if str(g.get("status") or "").lower() in {"closed", "resolved", "done", "completed"}
        )

        total_expected = total_expected_medications + total_expected_labs + total_expected_screenings
        if total_expected <= 0:
            return 100.0

        total_present = 0
        total_present += min(present_medications, total_expected_medications)
        total_present += min(present_labs, total_expected_labs)
        total_present += min(resolved_screenings, total_expected_screenings)

        return round((total_present / total_expected) * 100.0, 2)

    def _compute_avg_confidence(self) -> float:
        nodes = self.phig.get("nodes", [])
        confidences = [n["confidence"] for n in nodes if "confidence" in n]
        if not confidences:
            return 0.0
        return (sum(confidences) / len(confidences)) * 100.0

    def _compute_interaction_risk(self) -> float:
        interactions = self.phig.get("interactions", [])
        score = 100.0
        for ix in interactions:
            severity = ix.get("severity", "").lower()
            penalty = SEVERITY_PENALTIES.get(severity, 0)
            if ix.get("acknowledged", False):
                penalty *= 0.5
            score -= penalty
        return max(score, 0.0)

    def _compute_care_gap_status(self) -> float:
        care_gaps = self.phig.get("care_gaps", [])
        open_gaps = sum(1 for g in care_gaps if g.get("status") == "open")
        score = 100.0 - (open_gaps * 20)
        return max(score, 0.0)

    def _compute_adherence_rate(self) -> float:
        reminders = self.phig.get("reminders")
        if not reminders:
            return 75.0
        taken = reminders.get("taken", 0)
        skipped = reminders.get("skipped", 0)
        no_response = reminders.get("no_response", 0)
        total = taken + skipped + no_response
        if total == 0:
            return 75.0
        return (taken / total) * 100.0

    def compute(self) -> dict:
        breakdown = {
            "completeness": self._compute_completeness(),
            "avg_confidence": self._compute_avg_confidence(),
            "interaction_risk": self._compute_interaction_risk(),
            "care_gap_status": self._compute_care_gap_status(),
            "adherence_rate": self._compute_adherence_rate(),
        }
        total = sum(WEIGHTS[k] * v for k, v in breakdown.items())
        total = max(0.0, min(total, 100.0))
        self._score = total
        return {
            "total_score": total,
            "breakdown": breakdown,
            "delta": None,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

    def compute_delta(self, previous) -> float | None:
        if previous is None:
            return None
        if self._score is None:
            self.compute()
        return self._score - previous

    async def save_to_history(self, db, patient_id: str, score: float):
        query = "INSERT INTO orbit_score_history (patient_id, score, computed_at) VALUES (:patient_id, :score, :computed_at)"
        params = {
            "patient_id": patient_id,
            "score": score,
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.execute(query, params)
        await db.commit()
