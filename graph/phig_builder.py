import json
from uuid import UUID

from services.azure_search import AzureSearchService
from db.seed_demo import (
    get_seed_list_for_patient,
)
from db.session import async_session
from db.runtime_store import get_extracted_medications, get_latest_lab_markers

search_service = AzureSearchService()


class PHIGBuilder:
    @staticmethod
    def _normalize_uuid(value: str | None) -> str | None:
        if not value:
            return None
        try:
            return str(UUID(str(value)))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _confidence_label(score: float) -> str:
        if score >= 0.9:
            return "VERIFIED"
        if score >= 0.8:
            return "HIGH"
        if score >= 0.65:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def _safe_json(value):
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return json.loads(value)
            except Exception:
                return {}
        return {}

    async def _get_db_medication_subgraph(self, patient_id: str) -> dict:
        normalized_patient_id = self._normalize_uuid(patient_id)
        if not normalized_patient_id:
            return {"medications": []}

        try:
            async with async_session() as session:
                nodes_result = await session.execute(
                    "SELECT id, display_name, dosage, frequency, confidence_score, metadata "
                    "FROM phig_nodes "
                    "WHERE patient_id = :pid "
                    "AND node_type = CAST('medication' AS node_type) "
                    "AND is_active = TRUE",
                    {"pid": normalized_patient_id},
                )
                rows = nodes_result.mappings().all()

                meds = []
                meds_by_id: dict[str, dict] = {}
                meds_by_name: dict[str, dict] = {}

                for row in rows:
                    metadata = self._safe_json(row.get("metadata"))
                    confidence = float(row.get("confidence_score") or 0.0)
                    medication = {
                        "name": row.get("display_name") or "",
                        "dosage": row.get("dosage") or "",
                        "frequency": row.get("frequency") or "",
                        "confidence": confidence,
                        "confidence_label": metadata.get("confidence_label") or self._confidence_label(confidence),
                        "prescribed_by_doctor": metadata.get("prescribed_by_doctor"),
                        "coding": metadata.get("coding") or [],
                        "interactions": [],
                    }
                    meds.append(medication)
                    if row.get("id"):
                        meds_by_id[str(row.get("id"))] = medication
                    if medication["name"]:
                        meds_by_name[medication["name"].strip().lower()] = medication

                if not meds:
                    return {"medications": []}

                edges_result = await session.execute(
                    "SELECT e.source_node_id, e.target_node_id, e.severity, e.description, e.clinical_action, e.metadata, "
                    "s.display_name AS source_name, t.display_name AS target_name "
                    "FROM phig_edges e "
                    "JOIN phig_nodes s ON s.id = e.source_node_id "
                    "JOIN phig_nodes t ON t.id = e.target_node_id "
                    "WHERE e.patient_id = :pid AND e.edge_type = 'interaction' AND e.is_active = TRUE",
                    {"pid": normalized_patient_id},
                )
                edge_rows = edges_result.mappings().all()

                for edge in edge_rows:
                    source_id = str(edge.get("source_node_id") or "")
                    source_name = str(edge.get("source_name") or "")
                    target_name = str(edge.get("target_name") or "")

                    source_med = meds_by_id.get(source_id) or meds_by_name.get(source_name.strip().lower())
                    if not source_med:
                        continue

                    interaction_metadata = self._safe_json(edge.get("metadata"))
                    interaction = {
                        "drug_pair": interaction_metadata.get("drug_pair") or f"{source_name} + {target_name}",
                        "severity": edge.get("severity") or interaction_metadata.get("severity") or "unknown",
                        "description": edge.get("description") or interaction_metadata.get("description") or "",
                        "clinical_action": edge.get("clinical_action") or interaction_metadata.get("clinical_action") or "",
                    }
                    source_med["interactions"].append(interaction)

                return {"medications": meds}
        except Exception:
            return {"medications": []}

    async def check_interactions_for_node(self, patient_id: str, medication_node_id: str) -> list:
        interactions_data = await search_service.search_drug_interactions(medication_node_id)

        if not interactions_data:
            return []

        results = []
        patient_labs = await self._get_patient_labs(patient_id)

        for interaction in interactions_data:
            alert = {
                "drug_pair": interaction.get("drug_pair", ""),
                "severity": interaction.get("severity", "Unknown"),
                "description": interaction.get("description", ""),
                "clinical_action": interaction.get("clinical_action", ""),
            }

            modifiers = interaction.get("severity_modifiers", {})
            if modifiers and patient_labs:
                renal_mod = modifiers.get("renal_impairment")
                if renal_mod:
                    has_renal_issue = False
                    for lab in patient_labs:
                        if lab.get("loinc") == "2160-0" and lab.get("value", 0) > 1.3:
                            has_renal_issue = True
                        if lab.get("loinc") == "33914-3" and lab.get("value", 999) < 60:
                            has_renal_issue = True
                    if has_renal_issue:
                        alert["severity"] = renal_mod.get("escalation", alert["severity"])

            results.append(alert)

        return results

    async def _get_patient_labs(self, patient_id: str) -> list:
        return get_seed_list_for_patient(patient_id, "labs")

    async def get_medication_subgraph(self, patient_id: str) -> dict:
        db_subgraph = await self._get_db_medication_subgraph(patient_id)

        seed_meds = get_seed_list_for_patient(patient_id, "medications")
        seed_interactions = get_seed_list_for_patient(patient_id, "interactions")
        if seed_meds:
            meds = []
            for med in seed_meds:
                med_entry = {
                    "name": med["name"],
                    "dosage": med["dosage"],
                    "frequency": med["frequency"],
                    "confidence": med["confidence"],
                    "confidence_label": med["confidence_label"],
                    "prescribed_by_doctor": med.get("prescribed_by_doctor"),
                    "interactions": [],
                }
                for ix in seed_interactions:
                    if med["name"] in ix["drug_pair"]:
                        med_entry["interactions"].append(ix)
                meds.append(med_entry)

            for db_med in db_subgraph.get("medications", []):
                exists = next((m for m in meds if m.get("name", "").lower() == db_med.get("name", "").lower()), None)
                if exists:
                    exists.update({k: v for k, v in db_med.items() if k != "interactions" and v})
                    if db_med.get("interactions"):
                        exists["interactions"] = db_med["interactions"]
                else:
                    meds.append(dict(db_med))

            # Runtime extracted medications from uploaded documents.
            for med in get_extracted_medications(patient_id):
                exists = next((m for m in meds if m.get("name", "").lower() == med.get("name", "").lower()), None)
                if exists:
                    exists.update({k: v for k, v in med.items() if k != "interactions" and v})
                else:
                    meds.append(dict(med))
            return {"medications": meds}
        if db_subgraph.get("medications"):
            return db_subgraph
        return {"medications": get_extracted_medications(patient_id)}

    async def get_full_patient_graph(self, patient_id: str) -> dict:
        seed_conditions = get_seed_list_for_patient(patient_id, "conditions")
        seed_labs = get_seed_list_for_patient(patient_id, "labs")
        seed_interactions = get_seed_list_for_patient(patient_id, "interactions")
        if seed_conditions or seed_labs:
            meds_sub = await self.get_medication_subgraph(patient_id)
            dynamic_markers = get_latest_lab_markers(patient_id)

            merged_labs = {lab.get("name"): dict(lab) for lab in seed_labs}
            for marker_name, marker in dynamic_markers.items():
                merged_labs[marker_name] = {
                    "name": marker_name,
                    "value": marker.get("value"),
                    "unit": marker.get("unit", ""),
                    "ref_low": marker.get("ref_low"),
                    "ref_high": marker.get("ref_high"),
                    "abnormal": True,
                    "reference_range": "",
                    "node_type": "lab_value",
                }

            merged_interactions = list(seed_interactions)
            for med in meds_sub["medications"]:
                for ix in med.get("interactions", []) or []:
                    if isinstance(ix, dict):
                        merged_interactions.append(ix)

            total = len(meds_sub["medications"]) + len(seed_conditions) + len(merged_labs)
            return {
                "summary": {
                    "total_nodes": total,
                    "conditions_count": len(seed_conditions),
                    "medications_count": len(meds_sub["medications"]),
                    "labs_count": len(merged_labs),
                },
                "medications": meds_sub["medications"],
                "conditions": seed_conditions,
                "labs": list(merged_labs.values()),
                "interactions": merged_interactions,
            }
        return {"summary": {"total_nodes": 0}}


phig_builder = PHIGBuilder()
