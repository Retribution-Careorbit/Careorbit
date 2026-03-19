from services.azure_search import AzureSearchService
from db.seed_demo import (
    DEMO_USER_ID, RAMESH_MEDICATIONS, RAMESH_CONDITIONS,
    RAMESH_LABS, RAMESH_INTERACTIONS,
)
from db.runtime_store import get_extracted_medications, get_latest_lab_markers

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
        # DEMO SEED — remove when Azure + DB available
        if patient_id == DEMO_USER_ID:
            meds = []
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

            # Runtime extracted medications from uploaded documents.
            for med in get_extracted_medications(patient_id):
                exists = next((m for m in meds if m.get("name", "").lower() == med.get("name", "").lower()), None)
                if exists:
                    exists.update({k: v for k, v in med.items() if k != "interactions" and v})
                else:
                    meds.append(dict(med))
            return {"medications": meds}
        # END DEMO SEED
        return {"medications": []}

    async def get_full_patient_graph(self, patient_id: str) -> dict:
        # DEMO SEED — remove when Azure + DB available
        if patient_id == DEMO_USER_ID:
            meds_sub = await self.get_medication_subgraph(patient_id)
            dynamic_markers = get_latest_lab_markers(patient_id)

            merged_labs = {lab.get("name"): dict(lab) for lab in RAMESH_LABS}
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

            merged_interactions = list(RAMESH_INTERACTIONS)
            med_names = {m.get("name", "").lower() for m in meds_sub["medications"]}
            if "metformin" in med_names and "ibuprofen" in med_names:
                has_met_ibuprofen = any("Metformin + Ibuprofen" == ix.get("drug_pair") for ix in merged_interactions)
                if not has_met_ibuprofen:
                    merged_interactions.append({
                        "drug_pair": "Metformin + Ibuprofen",
                        "severity": "ELEVATED",
                        "description": "Potential renal stress risk when used together.",
                        "clinical_action": "Review with physician and monitor renal panel.",
                        "acknowledged": False,
                    })

            total = len(meds_sub["medications"]) + len(RAMESH_CONDITIONS) + len(merged_labs)
            return {
                "summary": {
                    "total_nodes": total,
                    "conditions_count": len(RAMESH_CONDITIONS),
                    "medications_count": len(meds_sub["medications"]),
                    "labs_count": len(merged_labs),
                },
                "medications": meds_sub["medications"],
                "conditions": RAMESH_CONDITIONS,
                "labs": list(merged_labs.values()),
                "interactions": merged_interactions,
            }
        # END DEMO SEED
        return {"summary": {"total_nodes": 0}}


phig_builder = PHIGBuilder()
