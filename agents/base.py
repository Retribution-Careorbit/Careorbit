from __future__ import annotations

import json
from typing import Any

from db.session import async_session as db_session


class BaseAgent:
    """Shared PHIG traversal/write helpers with patient scoping and audit logging."""

    def __init__(self, patient_id: str, requesting_user_id: str, db_factory=None):
        self.patient_id = patient_id
        self.requesting_user_id = requesting_user_id
        self._db_factory = db_factory or db_session

    def _json(self, value: Any) -> dict:
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {}
        return {}

    async def get_medications(self) -> list[dict[str, Any]]:
        async with self._db_factory() as session:
            result = await session.execute(
                "SELECT id, display_name, dosage, frequency, rxnorm_code, confidence_score, metadata "
                "FROM phig_nodes "
                "WHERE patient_id = :pid "
                "AND node_type = CAST('medication' AS node_type) "
                "AND is_active = TRUE "
                "AND confidence_score >= 0.50 "
                "ORDER BY updated_at DESC",
                {"pid": self.patient_id},
            )
            rows = result.mappings().all()
            meds = []
            for row in rows:
                meds.append(
                    {
                        "id": str(row.get("id") or ""),
                        "name": row.get("display_name") or "",
                        "dosage": row.get("dosage") or "",
                        "frequency": row.get("frequency") or "",
                        "rxnorm_code": row.get("rxnorm_code") or "",
                        "confidence": float(row.get("confidence_score") or 0.0),
                        "metadata": self._json(row.get("metadata")),
                    }
                )
            return meds

    async def get_lab_results(self) -> list[dict[str, Any]]:
        async with self._db_factory() as session:
            result = await session.execute(
                "SELECT id, display_name, value, unit, loinc_code, metadata, created_at "
                "FROM phig_nodes "
                "WHERE patient_id = :pid "
                "AND node_type = CAST('lab_result' AS node_type) "
                "AND is_active = TRUE "
                "ORDER BY created_at DESC",
                {"pid": self.patient_id},
            )
            rows = result.mappings().all()
            labs = []
            for row in rows:
                metadata = self._json(row.get("metadata"))
                labs.append(
                    {
                        "id": str(row.get("id") or ""),
                        "name": row.get("display_name") or "",
                        "value": row.get("value"),
                        "unit": row.get("unit") or "",
                        "loinc_code": row.get("loinc_code") or "",
                        "metadata": metadata,
                        "created_at": row.get("created_at"),
                    }
                )
            return labs

    async def get_conditions(self) -> list[dict[str, Any]]:
        async with self._db_factory() as session:
            result = await session.execute(
                "SELECT id, display_name, icd10_code, metadata, created_at "
                "FROM phig_nodes "
                "WHERE patient_id = :pid "
                "AND node_type = CAST('condition' AS node_type) "
                "AND is_active = TRUE "
                "ORDER BY created_at DESC",
                {"pid": self.patient_id},
            )
            rows = result.mappings().all()
            conditions = []
            for row in rows:
                metadata = self._json(row.get("metadata"))
                conditions.append(
                    {
                        "id": str(row.get("id") or ""),
                        "name": row.get("display_name") or "",
                        "icd10_code": row.get("icd10_code") or "",
                        "metadata": metadata,
                        "created_at": row.get("created_at"),
                    }
                )
            return conditions

    async def write_node(self, node_type: str, display_name: str, data: dict, confidence: float = 0.95) -> str | None:
        # Use 'procedure' as a compatible PHIG node type for synthesized care-gap nodes.
        normalized_type = str(node_type or "").strip().lower()
        if normalized_type not in {"medication", "condition", "lab_result", "allergy", "procedure"}:
            normalized_type = "procedure"

        async with self._db_factory() as session:
            created = await session.execute(
                "INSERT INTO phig_nodes ("
                "patient_id, node_type, display_name, confidence_score, confidence_source, metadata"
                ") VALUES ("
                ":pid, CAST(:node_type AS node_type), :display_name, :confidence, 'agent', CAST(:metadata AS JSONB)"
                ") RETURNING id",
                {
                    "pid": self.patient_id,
                    "node_type": normalized_type,
                    "display_name": display_name,
                    "confidence": float(confidence),
                    "metadata": json.dumps(data or {}),
                },
            )
            row = created.mappings().first()
            node_id = str((row or {}).get("id") or "")

            await session.execute(
                "INSERT INTO audit_log (user_id, patient_id, action, metadata) "
                "VALUES (:uid, :pid, :action, CAST(:metadata AS JSONB))",
                {
                    "uid": self.requesting_user_id,
                    "pid": self.patient_id,
                    "action": "agent_write_node",
                    "metadata": json.dumps({"node_id": node_id, "node_type": normalized_type, "display_name": display_name}),
                },
            )
            await session.commit()
            return node_id or None

    async def write_edge(self, source_id: str, target_id: str, edge_type: str, metadata: dict | None = None, severity: str | None = None, description: str | None = None, clinical_action: str | None = None) -> str | None:
        if not source_id or not target_id:
            return None

        async with self._db_factory() as session:
            source_res = await session.execute(
                "SELECT patient_id FROM phig_nodes WHERE id = :nid",
                {"nid": source_id},
            )
            target_res = await session.execute(
                "SELECT patient_id FROM phig_nodes WHERE id = :nid",
                {"nid": target_id},
            )
            source = source_res.mappings().first()
            target = target_res.mappings().first()
            if not source or not target:
                return None
            if str(source.get("patient_id")) != str(self.patient_id) or str(target.get("patient_id")) != str(self.patient_id):
                raise PermissionError("Cannot create cross-patient PHIG edge")

            created = await session.execute(
                "INSERT INTO phig_edges ("
                "patient_id, source_node_id, target_node_id, edge_type, severity, description, clinical_action, metadata"
                ") VALUES ("
                ":pid, :src, :dst, :edge_type, :severity, :description, :clinical_action, CAST(:metadata AS JSONB)"
                ") RETURNING id",
                {
                    "pid": self.patient_id,
                    "src": source_id,
                    "dst": target_id,
                    "edge_type": str(edge_type or "relationship"),
                    "severity": severity,
                    "description": description,
                    "clinical_action": clinical_action,
                    "metadata": json.dumps(metadata or {}),
                },
            )
            row = created.mappings().first()
            edge_id = str((row or {}).get("id") or "")

            await session.execute(
                "INSERT INTO audit_log (user_id, patient_id, action, metadata) "
                "VALUES (:uid, :pid, :action, CAST(:metadata AS JSONB))",
                {
                    "uid": self.requesting_user_id,
                    "pid": self.patient_id,
                    "action": "agent_write_edge",
                    "metadata": json.dumps({"edge_id": edge_id, "source": source_id, "target": target_id, "edge_type": edge_type}),
                },
            )
            await session.commit()
            return edge_id or None
