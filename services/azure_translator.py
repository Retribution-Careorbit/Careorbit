import logging
from config import get_settings

logger = logging.getLogger("careorbit.services.translator")


class AzureTranslatorService:
    def __init__(self):
        settings = get_settings()
        self._endpoint = settings.AZURE_TRANSLATOR_ENDPOINT
        self._key = settings.AZURE_TRANSLATOR_KEY

    async def translate(self, text, target_lang, source_lang=None):
        if not self._endpoint or not self._key:
            raise NotImplementedError("Azure Translator not configured")

        try:
            import httpx
            url = f"{self._endpoint}/translate"
            params = {"api-version": "3.0", "to": target_lang}
            if source_lang:
                params["from"] = source_lang

            headers = {
                "Ocp-Apim-Subscription-Key": self._key,
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers, params=params,
                    json=[{"text": text}],
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

            if data and len(data) > 0:
                translations = data[0].get("translations", [])
                if translations:
                    return translations[0]["text"]
            return text
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise

    async def detect_language(self, text):
        if not self._endpoint or not self._key:
            raise NotImplementedError("Azure Translator not configured")

        try:
            import httpx
            url = f"{self._endpoint}/detect"
            headers = {
                "Ocp-Apim-Subscription-Key": self._key,
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url, headers=headers,
                    params={"api-version": "3.0"},
                    json=[{"text": text}],
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()

            if data and len(data) > 0:
                return {
                    "language": data[0].get("language", "unknown"),
                    "confidence": float(data[0].get("score", 0.0)),
                }
            return {"language": "unknown", "confidence": 0.0}
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise
