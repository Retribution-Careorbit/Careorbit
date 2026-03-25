import json
import logging
import os
from config import get_settings

logger = logging.getLogger("careorbit.services.openai")


class AzureOpenAIService:
    def __init__(self):
        settings = get_settings()
        self._endpoint = settings.AZURE_OPENAI_ENDPOINT
        self._key = settings.AZURE_OPENAI_KEY
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._endpoint or not self._key:
            return None
        try:
            from openai import AzureOpenAI
            self._client = AzureOpenAI(
                azure_endpoint=self._endpoint,
                api_key=self._key,
                api_version="2024-02-01",
            )
            return self._client
        except Exception as e:
            logger.warning(f"Failed to initialize Azure OpenAI client: {e}")
            return None

    @staticmethod
    def _normalize_structured_payload(payload: dict) -> dict:
        medications = []
        for med in payload.get("medications", []) or []:
            medications.append(
                {
                    "name": str(med.get("name") or "").strip(),
                    "rxnorm": str(med.get("rxnorm") or med.get("rxnorm_id") or "").strip(),
                    "dosage": str(med.get("dosage") or med.get("dose") or "").strip(),
                    "frequency": str(med.get("frequency") or "").strip(),
                    "confidence": float(med.get("confidence") or 0.0),
                }
            )

        lab_results = []
        source_labs = payload.get("lab_results") or payload.get("labs") or []
        for lab in source_labs:
            lab_results.append(
                {
                    "name": str(lab.get("name") or "").strip(),
                    "value": lab.get("value"),
                    "unit": str(lab.get("unit") or "").strip(),
                    "flag": str(lab.get("flag") or "").strip(),
                    "confidence": float(lab.get("confidence") or 0.0),
                    "ref_low": lab.get("ref_low"),
                    "ref_high": lab.get("ref_high"),
                    "loinc": str(lab.get("loinc") or "").strip(),
                }
            )

        conditions = []
        for cond in payload.get("conditions", []) or []:
            conditions.append(
                {
                    "name": str(cond.get("name") or "").strip(),
                    "icd10": str(cond.get("icd10") or cond.get("code") or "").strip(),
                    "confidence": float(cond.get("confidence") or 0.0),
                }
            )

        return {
            "doctor_name": str(payload.get("doctor_name") or "").strip(),
            "summary": str(payload.get("summary") or "").strip(),
            "medications": medications,
            "lab_results": lab_results,
            "conditions": conditions,
            # Backward-compatible alias for existing pipeline keys.
            "labs": lab_results,
            "date": payload.get("date"),
        }

    async def extract_structured_data(self, text, doc_type):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure OpenAI not configured")

        system_prompt = (
            f"Extract structured medical data from this {doc_type}. "
            "Return only valid JSON and strictly follow this schema: "
            "{\"medications\":[{\"name\":string,\"rxnorm\":string,\"dose\":string,\"frequency\":string,\"confidence\":number}],"
            "\"lab_results\":[{\"name\":string,\"value\":number,\"unit\":string,\"flag\":string,\"confidence\":number}],"
            "\"conditions\":[{\"name\":string,\"icd10\":string,\"confidence\":number}],"
            "\"doctor_name\":string,\"summary\":string}. "
            "If a field is unknown, use empty string, 0, null, or empty array as appropriate. "
            "Use Indian medical terminology where appropriate."
        )
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
            raw = json.loads(response.choices[0].message.content)
            return self._normalize_structured_payload(raw if isinstance(raw, dict) else {})
        except Exception as e:
            logger.error(f"OpenAI extract_structured_data failed: {e}")
            raise

    async def chat(self, messages):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure OpenAI not configured")

        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat failed: {e}")
            raise

    async def chat_with_history(self, messages, context=None):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure OpenAI not configured")

        system_msg = (
            "You are CareOrbit AI, a healthcare assistant for Indian patients. "
            "Provide accurate, empathetic medical guidance in simple language. "
            "Always recommend consulting a doctor for serious concerns."
        )
        if context:
            system_msg += f"\nPatient context: {json.dumps(context)}"

        full_messages = [{"role": "system", "content": system_msg}] + messages

        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        try:
            response = client.chat.completions.create(
                model=deployment,
                messages=full_messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat_with_history failed: {e}")
            raise
