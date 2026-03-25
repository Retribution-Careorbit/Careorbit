from services.azure_openai import AzureOpenAIService
from services.azure_translator import AzureTranslatorService
from db.session import async_session as db_session
from graph.phig_builder import phig_builder
from agents.contracts import HistoryDeltaResult

openai_service = AzureOpenAIService()
translator_service = AzureTranslatorService()


def _build_narrative(patient_name, phig_nodes, trigger_event):
    medications = [n for n in phig_nodes if n.get("type") == "medication"]
    conditions = [n for n in phig_nodes if n.get("type") == "condition"]
    labs = [n for n in phig_nodes if n.get("type") == "lab_value"]

    parts = []
    parts.append(f"{patient_name}'s health overview")

    if trigger_event == "document_upload":
        parts.append("was updated after a new document was uploaded")
    elif trigger_event == "confirmation":
        parts.append("was updated following a data confirmation")
    elif trigger_event == "lab_added":
        parts.append("was updated with new lab results")
    elif trigger_event == "interaction_detected":
        parts.append("was updated due to a detected drug interaction")
    else:
        parts.append("has been refreshed")

    narrative = ". ".join(parts) + ". "

    if conditions:
        cond_names = [c["name"] for c in conditions]
        narrative += f"{patient_name} has been diagnosed with {', '.join(cond_names)}. "

    if medications:
        med_details = [f"{m['name']} ({m.get('dosage', '')})" for m in medications]
        narrative += f"Current medications include {', '.join(med_details)}. "

    if labs:
        lab_details = [f"{l['name']}: {l.get('value', '')} {l.get('unit', '')}" for l in labs]
        narrative += f"Recent lab results show {', '.join(lab_details)}. "

    narrative += f"This narrative was generated for {patient_name} based on available health records."

    return narrative


async def generate_living_narrative(patient_id, patient_name, phig_nodes, trigger_event, language="en"):
    import sys
    mod = sys.modules[__name__]
    _openai = mod.openai_service
    _translator = mod.translator_service
    _db = mod.db_session

    narrative = _build_narrative(patient_name, phig_nodes, trigger_event)

    narrative_text_hi = None
    if language == "hi":
        narrative_text_hi = await _translator.translate(narrative, "hi")

    await _db.execute(
        "INSERT INTO health_narratives (patient_id, narrative_text, narrative_text_hi, trigger_event, language) "
        "VALUES (:patient_id, :narrative_text, :narrative_text_hi, :trigger_event, :language)",
        {
            "patient_id": patient_id,
            "narrative_text": narrative,
            "narrative_text_hi": narrative_text_hi,
            "trigger_event": trigger_event,
            "language": language,
        }
    )
    await _db.commit()

    return narrative


class HistoryAgent:
    def __init__(self):
        pass

    async def generate_living_narrative(self, patient_id, patient_name, phig_nodes, trigger_event, language="en"):
        return await generate_living_narrative(patient_id, patient_name, phig_nodes, trigger_event, language)


class GraphHistoryAgent:
    """Traverse current PHIG state and produce deterministic narrative deltas."""

    def __init__(self, openai_client=None, translator=None):
        import sys

        mod = sys.modules[__name__]
        self._openai = openai_client or mod.openai_service
        self._translator = translator or mod.translator_service

    @staticmethod
    def _build_delta(phig: dict) -> str:
        lines = []

        meds = phig.get("medications", []) or []
        labs = phig.get("labs", []) or []
        interactions = phig.get("interactions", []) or []
        care_gaps = phig.get("care_gaps", []) or []

        for med in meds[:6]:
            name = med.get("name") or "Unknown"
            dosage = med.get("dosage") or ""
            lines.append(f"Medication active: {name} {dosage}".strip())

        for lab in labs[:6]:
            name = lab.get("name") or "Unknown"
            value = lab.get("value")
            unit = lab.get("unit") or ""
            lines.append(f"Lab observed: {name} = {value} {unit}".strip())

        for ix in interactions[:6]:
            pair = ix.get("drug_pair") or "Unknown pair"
            sev = ix.get("severity") or "unknown"
            lines.append(f"Interaction: {pair} severity {sev}")

        for gap in care_gaps[:6]:
            name = gap.get("name") or gap.get("screening") or "Care gap"
            lines.append(f"Care gap: {name}")

        if not lines:
            return "No significant PHIG changes detected."
        return "; ".join(lines)

    async def run(self, patient_id: str, language: str = "en") -> HistoryDeltaResult:
        phig = await phig_builder.get_full_patient_graph(patient_id)
        delta_summary = self._build_delta(phig if isinstance(phig, dict) else {})

        narrative_text = delta_summary
        try:
            ai_text = await self._openai.chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "Rewrite the PHIG delta into 2-3 concise, factual lines. "
                            "Use only provided facts. Do not invent clinical details."
                        ),
                    },
                    {"role": "user", "content": f"PHIG delta: {delta_summary}"},
                ]
            )
            if isinstance(ai_text, str) and ai_text.strip():
                narrative_text = ai_text.strip()
        except Exception:
            narrative_text = delta_summary

        if language and language != "en":
            try:
                narrative_text = await self._translator.translate(narrative_text, language)
            except Exception:
                pass

        return HistoryDeltaResult(
            delta_summary=delta_summary,
            narrative_text=narrative_text,
            language=language or "en",
        )
