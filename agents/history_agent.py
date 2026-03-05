from services.azure_openai import AzureOpenAIService
from services.azure_translator import AzureTranslatorService
from db.session import async_session as db_session

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
