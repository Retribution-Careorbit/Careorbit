import logging
from dataclasses import dataclass
from config import get_settings

logger = logging.getLogger("careorbit.services.vision")


@dataclass
class OCRResult:
    full_text: str
    lines: list
    avg_confidence: float
    page_count: int


class AzureVisionService:
    def __init__(self):
        settings = get_settings()
        self._endpoint = settings.AZURE_DI_ENDPOINT
        self._key = settings.AZURE_DI_KEY
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self._endpoint or not self._key:
            return None
        try:
            from azure.ai.formrecognizer import DocumentAnalysisClient
            from azure.core.credentials import AzureKeyCredential
            self._client = DocumentAnalysisClient(
                endpoint=self._endpoint,
                credential=AzureKeyCredential(self._key),
            )
            return self._client
        except Exception as e:
            logger.warning(f"Failed to initialize Document Intelligence client: {e}")
            return None

    async def extract_text(self, image_bytes):
        client = self._get_client()
        if not client:
            raise NotImplementedError("Azure Vision not configured")

        try:
            poller = client.begin_analyze_document(
                "prebuilt-read", document=image_bytes
            )
            result = poller.result()

            lines = []
            confidences = []
            for page in result.pages:
                for line in page.lines:
                    lines.append(line.content)
                    if hasattr(line, "spans") and line.spans:
                        confidences.append(1.0)

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            full_text = "\n".join(lines)

            return OCRResult(
                full_text=full_text,
                lines=lines,
                avg_confidence=avg_confidence,
                page_count=len(result.pages),
            )
        except Exception as e:
            logger.error(f"Document Intelligence OCR failed: {e}")
            raise

    async def classify_document_type(self, ocr_result):
        if not ocr_result or not ocr_result.full_text:
            return "unknown"

        text_lower = ocr_result.full_text.lower()

        rx_keywords = ["rx", "prescription", "tab", "cap", "syrup", "mg", "ml", "dr.", "sig:"]
        lab_keywords = ["lab report", "test result", "hemoglobin", "glucose", "cholesterol", "cbc", "hba1c", "creatinine"]
        strip_keywords = ["mfg", "batch", "exp", "strip", "tablet", "blister"]

        rx_score = sum(1 for kw in rx_keywords if kw in text_lower)
        lab_score = sum(1 for kw in lab_keywords if kw in text_lower)
        strip_score = sum(1 for kw in strip_keywords if kw in text_lower)

        scores = {"prescription": rx_score, "lab_report": lab_score, "medicine_strip": strip_score}
        best = max(scores, key=scores.get)

        if scores[best] == 0:
            return "unknown"
        return best
