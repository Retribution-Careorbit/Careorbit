from services.azure_search import AzureSearchService

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
        return []

    async def get_medication_subgraph(self, patient_id: str) -> dict:
        return {"medications": []}

    async def get_full_patient_graph(self, patient_id: str) -> dict:
        return {"summary": {"total_nodes": 0}}


phig_builder = PHIGBuilder()
