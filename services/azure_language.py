import logging
from config import get_settings

logger = logging.getLogger("careorbit.services.language")


class AzureLanguageService:
    def __init__(self):
        settings = get_settings()
        self._endpoint = settings.AZURE_LANGUAGE_ENDPOINT
        self._key = settings.AZURE_LANGUAGE_KEY
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._endpoint or not self._key:
            return None
        try:
            from azure.ai.textanalytics import TextAnalyticsClient
            from azure.core.credentials import AzureKeyCredential
            self._client = TextAnalyticsClient(
                endpoint=self._endpoint,
                credential=AzureKeyCredential(self._key),
            )
            return self._client
        except Exception as e:
            logger.warning(f"Failed to initialize Text Analytics client: {e}")
            return None

    async def recognize_health_entities(self, text):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Language not configured")

        try:
            poller = client.begin_analyze_healthcare_entities([text])
            result = list(poller.result())
            entities = []
            for doc in result:
                if not doc.is_error:
                    for entity in doc.entities:
                        coding = []
                        for ds in getattr(entity, "data_sources", []) or []:
                            coding.append(
                                {
                                    "name": getattr(ds, "name", ""),
                                    "id": getattr(ds, "entity_id", ""),
                                }
                            )
                        entities.append({
                            "text": entity.text,
                            "category": entity.category,
                            "confidence": entity.confidence_score,
                            "offset": entity.offset,
                            "length": entity.length,
                            "coding": coding,
                        })
            return entities
        except Exception as e:
            logger.error(f"Health entity recognition failed: {e}")
            raise

    async def recognize_entities(self, text):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Language not configured")

        try:
            response = client.recognize_entities([text])
            entities = []
            for doc in response:
                if not doc.is_error:
                    for entity in doc.entities:
                        entities.append({
                            "text": entity.text,
                            "category": entity.category,
                            "confidence": entity.confidence_score,
                            "offset": entity.offset,
                            "length": entity.length,
                        })
            return entities
        except Exception as e:
            logger.error(f"Entity recognition failed: {e}")
            raise
