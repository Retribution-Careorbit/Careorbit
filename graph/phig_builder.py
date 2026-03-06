from services.azure_search import AzureSearchService
from db.seed_demo import (
    DEMO_USER_ID, RAMESH_MEDICATIONS, RAMESH_CONDITIONS,
    RAMESH_LABS, RAMESH_INTERACTIONS,
)

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
                    "interactions": [],
                }
                for ix in RAMESH_INTERACTIONS:
                    if med["name"] in ix["drug_pair"]:
                        med_entry["interactions"].append(ix)
                meds.append(med_entry)
            return {"medications": meds}
        # END DEMO SEED
        return {"medications": []}

    async def get_full_patient_graph(self, patient_id: str) -> dict:
        # DEMO SEED — remove when Azure + DB available
        if patient_id == DEMO_USER_ID:
            total = len(RAMESH_MEDICATIONS) + len(RAMESH_CONDITIONS) + len(RAMESH_LABS)
            meds_sub = await self.get_medication_subgraph(patient_id)
            return {
                "summary": {
                    "total_nodes": total,
                    "conditions_count": len(RAMESH_CONDITIONS),
                    "medications_count": len(RAMESH_MEDICATIONS),
                    "labs_count": len(RAMESH_LABS),
                },
                "medications": meds_sub["medications"],
                "conditions": RAMESH_CONDITIONS,
                "labs": RAMESH_LABS,
                "interactions": RAMESH_INTERACTIONS,
            }
        # END DEMO SEED
        return {"summary": {"total_nodes": 0}}


phig_builder = PHIGBuilder()
