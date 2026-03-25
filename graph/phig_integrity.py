from __future__ import annotations

import json
from uuid import UUID, uuid4

from db.session import async_session

_in_memory_snapshots: dict[str, dict[str, dict]] = {}

LAB_RULES = {
    "hba1c": {"loinc": "4548-4", "units": {"%"}, "min": 2.0, "max": 20.0},
    "creatinine": {"loinc": "2160-0", "units": {"mg/dl"}, "min": 0.1, "max": 20.0},
    "egfr": {"loinc": "33914-3", "units": {"ml/min", "ml/min/1.73m2"}, "min": 1.0, "max": 200.0},
    "tsh": {"loinc": "3016-3", "units": {"uiu/ml", "miu/l"}, "min": 0.01, "max": 150.0},
    "alt": {"loinc": "1742-6", "units": {"u/l"}, "min": 1.0, "max": 2000.0},
}


def _normalize_uuid(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError):
        return None


def _safe_json(value):
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


class PHIGIntegrity:
    @staticmethod
    def _normalize_unit(unit: str | None) -> str:
        return str(unit or "").strip().lower()

    @staticmethod
    def _is_lab_value_unit_plausible(name: str, value: float | int | None, unit: str | None, loinc: str | None = None) -> bool:
        if value is None:
            return False
        try:
            value_f = float(value)
        except (TypeError, ValueError):
            return False

        rule = LAB_RULES.get(str(name or "").strip().lower())
        if not rule:
            return True

        if loinc and str(loinc).strip() and str(rule["loinc"]).lower() != str(loinc).strip().lower():
            return False

        unit_normalized = PHIGIntegrity._normalize_unit(unit)
        if unit_normalized and unit_normalized not in rule["units"]:
            return False

        return rule["min"] <= value_f <= rule["max"]

    async def create_snapshot(self, patient_id: str, reason: str = "") -> str:
        snapshot_id = str(uuid4())
        normalized_patient_id = _normalize_uuid(patient_id)
        if not normalized_patient_id:
            _in_memory_snapshots.setdefault(patient_id, {})[snapshot_id] = {
                "patient_id": patient_id,
                "reason": reason,
                "nodes": [],
                "edges": [],
            }
            return snapshot_id

        try:
            async with async_session() as session:
                nodes_result = await session.execute(
                    "SELECT id, patient_id, document_id, node_type, display_name, rxnorm_code, loinc_code, icd10_code, "
                    "dosage, frequency, value, unit, reference_range_low, reference_range_high, is_abnormal, "
                    "confidence_score, confidence_source, is_active, metadata "
                    "FROM phig_nodes "
                    "WHERE patient_id = :pid "
                    "AND is_active = TRUE "
                    "AND ("
                    "node_type = CAST('medication' AS node_type) "
                    "OR node_type = CAST('lab_result' AS node_type)"
                    ")",
                    {"pid": normalized_patient_id},
                )
                nodes = [dict(row) for row in nodes_result.mappings().all()]

                edges_result = await session.execute(
                    "SELECT id, patient_id, source_node_id, target_node_id, edge_type, severity, description, "
                    "clinical_action, metadata, is_active "
                    "FROM phig_edges "
                    "WHERE patient_id = :pid "
                    "AND is_active = TRUE "
                    "AND edge_type = 'interaction'",
                    {"pid": normalized_patient_id},
                )
                edges = [dict(row) for row in edges_result.mappings().all()]

            _in_memory_snapshots.setdefault(normalized_patient_id, {})[snapshot_id] = {
                "patient_id": normalized_patient_id,
                "reason": reason,
                "nodes": nodes,
                "edges": edges,
            }
            return snapshot_id
        except Exception:
            _in_memory_snapshots.setdefault(patient_id, {})[snapshot_id] = {
                "patient_id": patient_id,
                "reason": reason,
                "nodes": [],
                "edges": [],
            }
            return snapshot_id

    async def rollback_snapshot(self, patient_id: str, snapshot_id: str) -> bool:
        normalized_patient_id = _normalize_uuid(patient_id) or patient_id
        snapshot = (_in_memory_snapshots.get(normalized_patient_id) or {}).get(snapshot_id)
        if not snapshot:
            return False

        db_patient_id = _normalize_uuid(patient_id)
        if not db_patient_id:
            return True

        try:
            async with async_session() as session:
                await session.execute(
                    "UPDATE phig_edges SET is_active = FALSE "
                    "WHERE patient_id = :pid AND edge_type = 'interaction'",
                    {"pid": db_patient_id},
                )
                await session.execute(
                    "UPDATE phig_nodes SET is_active = FALSE "
                    "WHERE patient_id = :pid AND ("
                    "node_type = CAST('medication' AS node_type) "
                    "OR node_type = CAST('lab_result' AS node_type)"
                    ")",
                    {"pid": db_patient_id},
                )

                for node in snapshot.get("nodes", []):
                    await session.execute(
                        "UPDATE phig_nodes SET "
                        "patient_id = :patient_id, "
                        "document_id = :document_id, "
                        "node_type = CAST(:node_type AS node_type), "
                        "display_name = :display_name, "
                        "rxnorm_code = :rxnorm_code, "
                        "loinc_code = :loinc_code, "
                        "icd10_code = :icd10_code, "
                        "dosage = :dosage, "
                        "frequency = :frequency, "
                        "value = :value, "
                        "unit = :unit, "
                        "reference_range_low = :reference_range_low, "
                        "reference_range_high = :reference_range_high, "
                        "is_abnormal = :is_abnormal, "
                        "confidence_score = :confidence_score, "
                        "confidence_source = :confidence_source, "
                        "is_active = TRUE, "
                        "metadata = CAST(:metadata AS JSONB), "
                        "updated_at = NOW() "
                        "WHERE id = :id",
                        {
                            "id": str(node.get("id")),
                            "patient_id": str(node.get("patient_id")),
                            "document_id": str(node.get("document_id")) if node.get("document_id") else None,
                            "node_type": str(node.get("node_type")),
                            "display_name": node.get("display_name"),
                            "rxnorm_code": node.get("rxnorm_code"),
                            "loinc_code": node.get("loinc_code"),
                            "icd10_code": node.get("icd10_code"),
                            "dosage": node.get("dosage"),
                            "frequency": node.get("frequency"),
                            "value": node.get("value"),
                            "unit": node.get("unit"),
                            "reference_range_low": node.get("reference_range_low"),
                            "reference_range_high": node.get("reference_range_high"),
                            "is_abnormal": node.get("is_abnormal"),
                            "confidence_score": node.get("confidence_score"),
                            "confidence_source": node.get("confidence_source"),
                            "metadata": json.dumps(_safe_json(node.get("metadata"))),
                        },
                    )

                for edge in snapshot.get("edges", []):
                    await session.execute(
                        "UPDATE phig_edges SET "
                        "patient_id = :patient_id, "
                        "source_node_id = :source_node_id, "
                        "target_node_id = :target_node_id, "
                        "edge_type = :edge_type, "
                        "severity = :severity, "
                        "description = :description, "
                        "clinical_action = :clinical_action, "
                        "metadata = CAST(:metadata AS JSONB), "
                        "is_active = TRUE "
                        "WHERE id = :id",
                        {
                            "id": str(edge.get("id")),
                            "patient_id": str(edge.get("patient_id")),
                            "source_node_id": str(edge.get("source_node_id")),
                            "target_node_id": str(edge.get("target_node_id")),
                            "edge_type": edge.get("edge_type"),
                            "severity": edge.get("severity"),
                            "description": edge.get("description"),
                            "clinical_action": edge.get("clinical_action"),
                            "metadata": json.dumps(_safe_json(edge.get("metadata"))),
                        },
                    )

                await session.commit()
            return True
        except Exception:
            return False

    async def verify_consistency(self, patient_id: str) -> dict:
        normalized_patient_id = _normalize_uuid(patient_id)
        if not normalized_patient_id:
            return {"passed": True, "errors": []}

        errors: list[str] = []
        try:
            async with async_session() as session:
                orphan_result = await session.execute(
                    "SELECT e.id "
                    "FROM phig_edges e "
                    "LEFT JOIN phig_nodes s ON s.id = e.source_node_id AND s.is_active = TRUE "
                    "LEFT JOIN phig_nodes t ON t.id = e.target_node_id AND t.is_active = TRUE "
                    "WHERE e.patient_id = :pid "
                    "AND e.edge_type = 'interaction' "
                    "AND e.is_active = TRUE "
                    "AND (s.id IS NULL OR t.id IS NULL) "
                    "LIMIT 1",
                    {"pid": normalized_patient_id},
                )
                if orphan_result.mappings().first():
                    errors.append("orphan_interaction_edge")

                duplicate_result = await session.execute(
                    "SELECT source_node_id, target_node_id "
                    "FROM phig_edges "
                    "WHERE patient_id = :pid "
                    "AND edge_type = 'interaction' "
                    "AND is_active = TRUE "
                    "GROUP BY source_node_id, target_node_id "
                    "HAVING COUNT(*) > 1 "
                    "LIMIT 1",
                    {"pid": normalized_patient_id},
                )
                if duplicate_result.mappings().first():
                    errors.append("duplicate_interaction_edges")

                malformed_medication_result = await session.execute(
                    "SELECT id FROM phig_nodes "
                    "WHERE patient_id = :pid "
                    "AND node_type = CAST('medication' AS node_type) "
                    "AND is_active = TRUE "
                    "AND (display_name IS NULL OR display_name = '' OR dosage IS NULL OR dosage = '') "
                    "LIMIT 1",
                    {"pid": normalized_patient_id},
                )
                if malformed_medication_result.mappings().first():
                    errors.append("malformed_medication_node")

                malformed_lab_result = await session.execute(
                    "SELECT id FROM phig_nodes "
                    "WHERE patient_id = :pid "
                    "AND node_type = CAST('lab_result' AS node_type) "
                    "AND is_active = TRUE "
                    "AND (display_name IS NULL OR display_name = '' OR value IS NULL OR unit IS NULL OR unit = '') "
                    "LIMIT 1",
                    {"pid": normalized_patient_id},
                )
                if malformed_lab_result.mappings().first():
                    errors.append("malformed_lab_result_node")

                labs_result = await session.execute(
                    "SELECT display_name, value, unit, loinc_code "
                    "FROM phig_nodes "
                    "WHERE patient_id = :pid "
                    "AND node_type = CAST('lab_result' AS node_type) "
                    "AND is_active = TRUE",
                    {"pid": normalized_patient_id},
                )
                for lab in labs_result.mappings().all():
                    if not self._is_lab_value_unit_plausible(
                        name=str(lab.get("display_name") or ""),
                        value=lab.get("value"),
                        unit=str(lab.get("unit") or ""),
                        loinc=str(lab.get("loinc_code") or ""),
                    ):
                        errors.append("impossible_lab_value_unit")
                        break

            return {"passed": not errors, "errors": errors}
        except Exception:
            return {"passed": False, "errors": ["consistency_check_failed"]}


phig_integrity = PHIGIntegrity()
