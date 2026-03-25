from __future__ import annotations

from datetime import date, datetime

from agents.base import BaseAgent
from agents.contracts import CareGapResult


class CareGapAgent(BaseAgent):
    """Detect overdue screenings via exact ICD-10 guideline retrieval and PHIG traversal."""

    def __init__(self, patient_id: str, requesting_user_id: str, search_client, db_factory=None):
        super().__init__(patient_id=patient_id, requesting_user_id=requesting_user_id, db_factory=db_factory)
        self.search_client = search_client

    @staticmethod
    def _years_since(value) -> float:
        if value is None:
            return 0.0
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                try:
                    parsed = datetime.strptime(value[:10], "%Y-%m-%d")
                except Exception:
                    return 0.0
        elif isinstance(value, datetime):
            parsed = value
        else:
            try:
                parsed = datetime.combine(value, datetime.min.time())
            except Exception:
                return 0.0

        now = datetime.utcnow()
        delta_days = max((now - parsed).days, 0)
        return round(delta_days / 365.25, 2)

    async def _latest_screening_years_since(self, screening_name: str) -> float | None:
        async with self._db_factory() as session:
            result = await session.execute(
                "SELECT created_at FROM phig_nodes "
                "WHERE patient_id = :pid "
                "AND node_type = CAST('lab_result' AS node_type) "
                "AND LOWER(display_name) = :screening_name "
                "AND is_active = TRUE "
                "ORDER BY created_at DESC LIMIT 1",
                {
                    "pid": self.patient_id,
                    "screening_name": str(screening_name or "").strip().lower(),
                },
            )
            row = result.mappings().first()
            if not row:
                return None
            return self._years_since(row.get("created_at"))

    async def run(self) -> list[CareGapResult]:
        conditions = await self.get_conditions()
        if not conditions:
            return []

        gaps: list[CareGapResult] = []

        for condition in conditions:
            icd10 = str(condition.get("icd10_code") or "").strip().upper()
            if not icd10:
                continue

            guidelines = await self.search_client.find_guidelines_exact(icd10)
            for guideline in guidelines:
                validation = self.search_client.validator.validate_guideline(query_icd10=icd10, result=guideline)
                if not validation.valid:
                    continue

                screening_name = str(guideline.get("screening_name") or guideline.get("screening") or "").strip()
                if not screening_name:
                    continue

                interval_years = float(guideline.get("interval_years") or 1.0)
                years_since = await self._latest_screening_years_since(screening_name)

                is_overdue = years_since is None or years_since >= interval_years
                if not is_overdue:
                    continue

                overdue_years = (years_since if years_since is not None else self._years_since(condition.get("created_at")))

                gap_node_id = await self.write_node(
                    node_type="procedure",
                    display_name=f"Care gap: {screening_name}",
                    confidence=0.95,
                    data={
                        "node_subtype": "care_gap",
                        "condition": condition.get("name"),
                        "condition_icd10": icd10,
                        "screening_required": screening_name,
                        "interval_years": interval_years,
                        "overdue_years": overdue_years,
                        "guideline_source": guideline.get("guideline_source") or guideline.get("source"),
                        "recommendation": guideline.get("recommendation") or "",
                    },
                )

                if gap_node_id:
                    await self.write_edge(
                        source_id=condition.get("id") or "",
                        target_id=gap_node_id,
                        edge_type="care_gap",
                        severity="HIGH" if overdue_years >= 3 else "MODERATE",
                        description=f"{screening_name} overdue",
                        clinical_action=str(guideline.get("recommendation") or ""),
                        metadata={
                            "semantic_edge_type": "HAS_GAP",
                            "guideline_source": guideline.get("guideline_source") or guideline.get("source"),
                            "condition_icd10": icd10,
                        },
                    )

                gaps.append(
                    CareGapResult(
                        condition=str(condition.get("name") or ""),
                        screening=screening_name,
                        overdue_years=float(overdue_years or 0.0),
                        guideline=str(guideline.get("guideline_source") or guideline.get("source") or ""),
                        recommendation=str(guideline.get("recommendation") or ""),
                        metadata={
                            "interval_years": interval_years,
                            "condition_icd10": icd10,
                        },
                    )
                )

        return gaps
