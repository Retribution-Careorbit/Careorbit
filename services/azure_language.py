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

    @staticmethod
    def _normalize_category(category: str) -> str:
        mapping = {
            "medicationname": "MedicationName",
            "medication": "MedicationName",
            "dosage": "Dosage",
            "medicationfrequency": "MedicationFrequency",
            "medicationroute": "MedicationRoute",
            "diagnosis": "Diagnosis",
            "symptomorsign": "SymptomOrSign",
            "bodystructure": "BodyStructure",
            "labvalue": "LabValue",
            "examinationname": "ExaminationName",
        }
        key = str(category or "").strip().lower()
        return mapping.get(key, str(category or "").strip() or "Unknown")

    @staticmethod
    def _extract_codes(coding: list[dict]) -> tuple[str | None, str | None]:
        rxnorm_id = None
        icd10_code = None
        for item in coding:
            source_name = str(item.get("name") or "").strip().lower()
            source_id = str(item.get("id") or "").strip()
            if not source_id:
                continue
            if "rxnorm" in source_name and not rxnorm_id:
                rxnorm_id = source_id
            if ("icd" in source_name or "icd-10" in source_name) and not icd10_code:
                icd10_code = source_id
        return rxnorm_id, icd10_code

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
                        rxnorm_id, icd10_code = self._extract_codes(coding)
                        normalized_category = self._normalize_category(entity.category)
                        entities.append({
                            "text": entity.text,
                            "category": normalized_category,
                            "confidence": entity.confidence_score,
                            "offset": entity.offset,
                            "length": entity.length,
                            "coding": coding,
                            "rxnorm_id": rxnorm_id,
                            "icd10_code": icd10_code,
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
