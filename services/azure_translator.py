import logging
import asyncio
from dataclasses import dataclass
from config import get_settings

logger = logging.getLogger("careorbit.services.translator")


@dataclass
class TranslationResult:
    translated_text: str
    detected_language: str
    confidence: float
    provider_status: str
    error_code: str | None = None


class AzureTranslatorService:
    def __init__(self):
        settings = get_settings()
        self._endpoint = settings.AZURE_TRANSLATOR_ENDPOINT
        self._key = settings.AZURE_TRANSLATOR_KEY
        self._timeout = max(int(getattr(settings, "CHAT_TRANSLATION_TIMEOUT_MS", 8000)), 1000) / 1000.0
        self._max_retries = max(int(getattr(settings, "CHAT_TRANSLATION_RETRIES", 2)), 0)

    async def _request_with_retry(self, call, operation: str):
        last_error = None
        for attempt in range(self._max_retries + 1):
            try:
                return await call()
            except Exception as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    break
                await asyncio.sleep(min(0.25 * (2 ** attempt), 1.0))

        logger.error(f"Translator {operation} failed after retries: {last_error}")
        raise last_error

    async def translate_with_metadata(self, text: str, target_lang: str, source_lang: str | None = None) -> TranslationResult:
        if not self._endpoint or not self._key:
            raise NotImplementedError("Azure Translator not configured")
        if text is None:
            text = ""

        try:
            import httpx

            async def _do_request():
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
                        url,
                        headers=headers,
                        params=params,
                        json=[{"text": text}],
                        timeout=self._timeout,
                    )
                    response.raise_for_status()
                    return response.json()

            data = await self._request_with_retry(_do_request, operation="translate")

            if data and len(data) > 0:
                detected = data[0].get("detectedLanguage") or {}
                translations = data[0].get("translations", [])
                if translations:
                    return TranslationResult(
                        translated_text=translations[0].get("text", text),
                        detected_language=str(detected.get("language") or source_lang or "unknown"),
                        confidence=float(detected.get("score") or 0.0),
                        provider_status="ok",
                        error_code=None,
                    )

            return TranslationResult(
                translated_text=text,
                detected_language=source_lang or "unknown",
                confidence=0.0,
                provider_status="empty",
                error_code="empty_response",
            )
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return TranslationResult(
                translated_text=text,
                detected_language=source_lang or "unknown",
                confidence=0.0,
                provider_status="error",
                error_code=str(type(e).__name__),
            )

    async def translate(self, text, target_lang, source_lang=None):
        result = await self.translate_with_metadata(text=text, target_lang=target_lang, source_lang=source_lang)
        if result.provider_status == "error":
            raise RuntimeError(f"Translator unavailable: {result.error_code}")
        return result.translated_text

    async def detect_language(self, text):
        if not self._endpoint or not self._key:
            raise NotImplementedError("Azure Translator not configured")

        try:
            import httpx

            async def _do_request():
                url = f"{self._endpoint}/detect"
                headers = {
                    "Ocp-Apim-Subscription-Key": self._key,
                    "Content-Type": "application/json",
                }

                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        headers=headers,
                        params={"api-version": "3.0"},
                        json=[{"text": text}],
                        timeout=self._timeout,
                    )
                    response.raise_for_status()
                    return response.json()

            data = await self._request_with_retry(_do_request, operation="detect")

            if data and len(data) > 0:
                return {
                    "language": data[0].get("language", "unknown"),
                    "confidence": float(data[0].get("score", 0.0)),
                }
            return {"language": "unknown", "confidence": 0.0}
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise
