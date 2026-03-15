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

    async def extract_structured_data(self, text, doc_type):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure OpenAI not configured")

        system_prompt = (
            f"Extract structured medical data from this {doc_type}. "
            "Return valid JSON with relevant fields like medications, dosages, "
            "diagnoses, lab values. Use Indian medical terminology where appropriate."
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
            return json.loads(response.choices[0].message.content)
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
