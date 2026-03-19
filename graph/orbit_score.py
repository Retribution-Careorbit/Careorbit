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
EXPECTED_NODES_PER_CONDITION = {
    "E11.9": {"medications": 1, "lab_results": 2, "screenings": 1},
    "I10": {"medications": 1, "lab_results": 1, "screenings": 0},
    "I48": {"medications": 1, "lab_results": 1, "screenings": 0},
}
SEVERITY_PENALTIES = {
    "elevated": 25,
    "moderate": 15,
    "low": 5,
}


class OrbitScoreCalculator:
    def __init__(self, phig: dict):
        self.phig = phig
        self._score = None

    def _legacy_type_completeness(self, nodes: list[dict]) -> float:
        present_types = {n.get("type") for n in nodes}
        core_count = len(CORE_TYPES & present_types)
        base = (core_count / len(CORE_TYPES)) * 100.0
        bonus = 0.0
        for bt in BONUS_TYPES:
            if bt in present_types:
                bonus += 5.0
        return min(base + bonus, 100.0)

    def _code_for_condition(self, node: dict) -> str | None:
        value = node.get("icd10") or node.get("code") or node.get("condition_code")
        if not value:
            return None
        return str(value).upper()

    def _node_type(self, value: str | None) -> str:
        mapping = {
            "medication": "medication",
            "lab_result": "lab_value",
            "condition": "condition",
        }
        return mapping.get(str(value or "").lower(), str(value or "").lower())

    def _compute_completeness(self) -> float:
        nodes = self.phig.get("nodes", [])
        edges = self.phig.get("edges", [])
        conditions = [n for n in nodes if n.get("type") == "condition"]
        if not conditions:
            return self._legacy_type_completeness(nodes)

        condition_codes = [self._code_for_condition(c) for c in conditions if self._code_for_condition(c)]
        if not condition_codes:
            return 0.0

        if not edges:
            return 0.0

        code_to_condition_ids: dict[str, set[str]] = {}
        id_to_type: dict[str, str] = {}
        for node in nodes:
            node_id = str(node.get("phig_node_id") or node.get("id") or "")
            if node_id:
                id_to_type[node_id] = self._node_type(node.get("type"))
            if node.get("type") == "condition":
                code = self._code_for_condition(node)
                if code and node_id:
                    code_to_condition_ids.setdefault(code, set()).add(node_id)

        if not code_to_condition_ids:
            return 0.0

        meds_by_code: dict[str, set[str]] = {code: set() for code in code_to_condition_ids}
        labs_by_code: dict[str, set[str]] = {code: set() for code in code_to_condition_ids}

        for edge in edges:
            edge_type = str(edge.get("edge_type") or "").upper()
            src = str(edge.get("source_node_id") or "")
            dst = str(edge.get("target_node_id") or "")
            src_type = self._node_type(edge.get("source_node_type") or id_to_type.get(src))
            dst_type = self._node_type(edge.get("target_node_type") or id_to_type.get(dst))

            if src_type != "condition":
                continue

            for code, cond_ids in code_to_condition_ids.items():
                if src not in cond_ids:
                    continue
                if edge_type in {"CONDITION_HAS_MEDICATION", "HAS_MEDICATION"} and dst_type == "medication":
                    meds_by_code[code].add(dst)
                if edge_type in {"CONDITION_HAS_LAB", "HAS_LAB"} and dst_type == "lab_value":
                    labs_by_code[code].add(dst)

        care_gaps = self.phig.get("care_gaps", [])
        total_expected = 0
        total_present = 0

        for icd_code in sorted(set(condition_codes)):
            expected = EXPECTED_NODES_PER_CONDITION.get(
                icd_code,
                {"medications": 1, "lab_results": 1, "screenings": 0},
            )
            total_expected += sum(expected.values())

            meds = len(meds_by_code.get(icd_code, set()))
            labs = len(labs_by_code.get(icd_code, set()))
            screenings = sum(
                1
                for g in care_gaps
                if (str(g.get("condition_code") or "").upper() in {"", icd_code})
                and str(g.get("status", "")).lower() in {"resolved", "closed", "completed"}
            )

            total_present += min(meds, expected["medications"])
            total_present += min(labs, expected["lab_results"])
            total_present += min(screenings, expected["screenings"])

        if total_expected == 0:
            return 100.0
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
        if isinstance(reminders, dict) and "adherence_rate" in reminders:
            rate = reminders.get("adherence_rate", 0)
            try:
                rate = float(rate)
            except (TypeError, ValueError):
                return 75.0
            if rate <= 1.0:
                return max(0.0, min(rate * 100.0, 100.0))
            return max(0.0, min(rate, 100.0))
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
