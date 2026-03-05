import ast
import json
from datetime import datetime, timezone

from services.azure_openai import AzureOpenAIService
from db.session import async_session as db_session

openai_service = AzureOpenAIService()


class PreVisitAgent:
    def __init__(self):
        import sys
        mod = sys.modules[__name__]
        self._openai = mod.openai_service
        self._db = mod.db_session

    async def generate_previsit_brief(self, appointment_id: str, phig: dict) -> dict:
        result = await self._db.execute(
            "SELECT * FROM appointments WHERE id = :appointment_id",
            {"appointment_id": appointment_id}
        )
        row = result.first()
        if row is None:
            raise ValueError(f"Appointment {appointment_id} not found")

        medications = phig.get("medications", [])
        conditions = phig.get("conditions", [])
        labs = phig.get("labs", [])
        interactions = phig.get("interactions", [])
        care_gaps = phig.get("care_gaps", [])

        med_summary = ", ".join(
            f"{m['name']} {m.get('dosage', '')}" for m in medications
        ) if medications else "No medications recorded"

        condition_summary = ", ".join(
            c["name"] for c in conditions
        ) if conditions else "No conditions recorded"

        lab_summary = ", ".join(
            f"{l['name']}: {l.get('value', '')} {l.get('unit', '')}" for l in labs
        ) if labs else "No lab results"

        interaction_summary = ", ".join(
            f"{i['drug_pair']} ({i.get('severity', '')})" for i in interactions
        ) if interactions else "No interactions"

        prompt = (
            f"Generate a pre-visit brief for an upcoming appointment.\n"
            f"Patient medications: {med_summary}\n"
            f"Conditions: {condition_summary}\n"
            f"Recent labs: {lab_summary}\n"
            f"Drug interactions: {interaction_summary}\n"
            f"Return a JSON object with keys: tell_doctor, ask_doctor, "
            f"doctor_may_not_know, bring_to_appointment, urgency_flags"
        )

        response = await self._openai.chat([
            {"role": "system", "content": "You are a pre-visit brief generator for CareOrbit."},
            {"role": "user", "content": prompt},
        ])

        brief = self._parse_response(response, phig)

        brief_json = json.dumps(brief)
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE appointments SET brief_content = :brief_content, "
            "brief_sent_at = :brief_sent_at WHERE id = :appointment_id",
            {"brief_content": brief_json, "brief_sent_at": now, "appointment_id": appointment_id}
        )
        await self._db.commit()

        return brief

    def _parse_response(self, response: str, phig: dict) -> dict:
        parsed = None
        try:
            parsed = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            try:
                parsed = ast.literal_eval(response)
            except (ValueError, SyntaxError):
                parsed = None

        if not isinstance(parsed, dict):
            parsed = {}

        medications = phig.get("medications", [])
        interactions = phig.get("interactions", [])

        brief = {
            "tell_doctor": parsed.get("tell_doctor", []),
            "ask_doctor": parsed.get("ask_doctor", []),
            "doctor_may_not_know": parsed.get("doctor_may_not_know", []),
            "bring_to_appointment": parsed.get("bring_to_appointment", []),
            "urgency_flags": parsed.get("urgency_flags", []),
        }

        if not isinstance(brief["tell_doctor"], list):
            brief["tell_doctor"] = [brief["tell_doctor"]] if brief["tell_doctor"] else []
        if not isinstance(brief["ask_doctor"], list):
            brief["ask_doctor"] = [brief["ask_doctor"]] if brief["ask_doctor"] else []
        if not isinstance(brief["doctor_may_not_know"], list):
            brief["doctor_may_not_know"] = [brief["doctor_may_not_know"]] if brief["doctor_may_not_know"] else []
        if not isinstance(brief["bring_to_appointment"], list):
            brief["bring_to_appointment"] = [brief["bring_to_appointment"]] if brief["bring_to_appointment"] else []
        if not isinstance(brief["urgency_flags"], list):
            brief["urgency_flags"] = [brief["urgency_flags"]] if brief["urgency_flags"] else []

        med_names_in_tell = set()
        for item in brief["tell_doctor"]:
            for m in medications:
                if m["name"].lower() in str(item).lower():
                    med_names_in_tell.add(m["name"])

        for med in medications:
            if med["name"] not in med_names_in_tell:
                brief["tell_doctor"].append(f"Taking {med['name']} {med.get('dosage', '')}")

        med_names_in_dmnk = set()
        for item in brief["doctor_may_not_know"]:
            for m in medications:
                if m["name"].lower() in str(item).lower():
                    med_names_in_dmnk.add(m["name"])

        for med in medications:
            if med["name"] not in med_names_in_dmnk:
                brief["doctor_may_not_know"].append(med["name"])

        for interaction in interactions:
            severity = interaction.get("severity", "")
            if severity in ("ELEVATED", "HIGH"):
                flag = f"{severity} interaction: {interaction['drug_pair']}"
                if flag not in brief["urgency_flags"]:
                    brief["urgency_flags"].append(flag)

        bring_text = " ".join(str(item).lower() for item in brief["bring_to_appointment"])
        if "health summary" not in bring_text and "pdf" not in bring_text:
            brief["bring_to_appointment"].append("Health summary PDF")

        if not brief["ask_doctor"]:
            brief["ask_doctor"].append("Review current medication regimen")

        return brief
