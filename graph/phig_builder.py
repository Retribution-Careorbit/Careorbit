from services.azure_search import AzureSearchService
from db.seed_demo import (
    DEMO_USER_ID, RAMESH_MEDICATIONS, RAMESH_CONDITIONS,
    RAMESH_LABS, RAMESH_INTERACTIONS, RAMESH_CARE_GAPS,
)
from db.runtime_store import get_extracted_medications, get_latest_lab_markers
from db.phig_repository import load_patient_graph_from_db

search_service = AzureSearchService()


class PHIGBuilder:
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
        # DEMO SEED — remove when Azure + DB available
        if patient_id == DEMO_USER_ID:
            return RAMESH_LABS
        # END DEMO SEED
        return []

    async def get_medication_subgraph(self, patient_id: str) -> dict:
        db_graph = await load_patient_graph_from_db(patient_id)
        if db_graph.get("from_db") and db_graph.get("medications"):
            return {"medications": db_graph.get("medications", [])}

        meds = []

        # DEMO SEED — remove when Azure + DB available
        if patient_id == DEMO_USER_ID:
            for med in RAMESH_MEDICATIONS:
                med_entry = {
                    "name": med["name"],
                    "dosage": med["dosage"],
                    "frequency": med["frequency"],
                    "confidence": med["confidence"],
                    "confidence_label": med["confidence_label"],
                    "prescribed_by_doctor": med.get("prescribed_by_doctor"),
                    "interactions": [],
                }
                for ix in RAMESH_INTERACTIONS:
                    if med["name"] in ix["drug_pair"]:
                        med_entry["interactions"].append(ix)
                meds.append(med_entry)
        # END DEMO SEED

        # Runtime extracted medications from uploaded documents should be visible for all users.
        for med in get_extracted_medications(patient_id):
            exists = next((m for m in meds if m.get("name", "").lower() == med.get("name", "").lower()), None)
            if exists:
                exists.update({k: v for k, v in med.items() if k != "interactions" and v})
            else:
                meds.append(dict(med))

        return {"medications": meds}

    async def get_full_patient_graph(self, patient_id: str) -> dict:
        db_graph = await load_patient_graph_from_db(patient_id)
        if db_graph.get("from_db"):
            medications = db_graph.get("medications", [])
            conditions = db_graph.get("conditions", [])
            labs = db_graph.get("labs", [])
            interactions = db_graph.get("interactions", [])
            care_gaps = db_graph.get("care_gaps", [])
            edges = db_graph.get("edges", [])
            total = len(medications) + len(conditions) + len(labs)
            return {
                "summary": {
                    "total_nodes": total,
                    "conditions_count": len(conditions),
                    "medications_count": len(medications),
                    "labs_count": len(labs),
                },
                "medications": medications,
                "conditions": conditions,
                "labs": labs,
                "interactions": interactions,
                "care_gaps": care_gaps,
                "edges": edges,
            }

        meds_sub = await self.get_medication_subgraph(patient_id)
        dynamic_markers = get_latest_lab_markers(patient_id)

        # DEMO SEED — remove when Azure + DB available
        base_labs = list(RAMESH_LABS) if patient_id == DEMO_USER_ID else []
        base_conditions = list(RAMESH_CONDITIONS) if patient_id == DEMO_USER_ID else []
        base_interactions = list(RAMESH_INTERACTIONS) if patient_id == DEMO_USER_ID else []
        base_care_gaps = list(RAMESH_CARE_GAPS) if patient_id == DEMO_USER_ID else []
        # END DEMO SEED

        merged_labs = {lab.get("name"): dict(lab) for lab in base_labs if lab.get("name")}
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

        merged_interactions = list(base_interactions)
        med_names = {m.get("name", "").lower() for m in meds_sub["medications"]}
        if patient_id == DEMO_USER_ID and "metformin" in med_names and "ibuprofen" in med_names:
            has_met_ibuprofen = any("Metformin + Ibuprofen" == ix.get("drug_pair") for ix in merged_interactions)
            if not has_met_ibuprofen:
                merged_interactions.append({
                    "drug_pair": "Metformin + Ibuprofen",
                    "severity": "ELEVATED",
                    "description": "Potential renal stress risk when used together.",
                    "clinical_action": "Review with physician and monitor renal panel.",
                    "acknowledged": False,
                })

        total = len(meds_sub["medications"]) + len(base_conditions) + len(merged_labs)
        return {
            "summary": {
                "total_nodes": total,
                "conditions_count": len(base_conditions),
                "medications_count": len(meds_sub["medications"]),
                "labs_count": len(merged_labs),
            },
            "medications": meds_sub["medications"],
            "conditions": base_conditions,
            "labs": list(merged_labs.values()),
            "interactions": merged_interactions,
            "care_gaps": base_care_gaps,
            "edges": [],
        }


phig_builder = PHIGBuilder()
