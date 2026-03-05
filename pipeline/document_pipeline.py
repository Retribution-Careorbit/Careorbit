from services.azure_openai import AzureOpenAIService
from services.azure_vision import AzureVisionService
from services.azure_blob import AzureBlobService
from services.azure_search import AzureSearchService
from services.azure_email import AzureEmailService
from db.session import async_session as db_session
from graph.confidence import ConfidenceCalculator
from graph.orbit_score import OrbitScoreCalculator
from utils.drug_database import DrugDatabase

openai_service = AzureOpenAIService()
vision_service = AzureVisionService()
blob_service = AzureBlobService()
search_service = AzureSearchService()
email_service = AzureEmailService()

CONFIDENCE_THRESHOLD = 0.70


class DocumentProcessingResult:
    def __init__(self, **kwargs):
        self.document_id = kwargs.get("document_id", "")
        self.document_type = kwargs.get("document_type", "unknown")
        self.processing_status = kwargs.get("processing_status", "success")
        self.nodes_created = kwargs.get("nodes_created", [])
        self.interaction_alerts = kwargs.get("interaction_alerts", [])
        self.care_gap_alerts = kwargs.get("care_gap_alerts", [])
        self.confirmation_needed = kwargs.get("confirmation_needed", [])
        self.processing_time_ms = kwargs.get("processing_time_ms", 0)
        self.error_message = kwargs.get("error_message", None)


class DocumentPipeline:
    def __init__(self):
        import sys
        mod = sys.modules[__name__]
        self._vision = mod.vision_service
        self._openai = mod.openai_service
        self._blob = mod.blob_service
        self._search = mod.search_service
        self._email = mod.email_service
        self._drug_db = DrugDatabase()

    async def process_document(self, image_bytes, patient_id, uploaded_by, file_extension="jpg"):
        import time
        start = time.time()

        try:
            ocr_result = await self._vision.extract_text(image_bytes)
        except Exception as e:
            return DocumentProcessingResult(
                document_id=f"doc-{patient_id}",
                document_type="unknown",
                processing_status="failed",
                error_message=str(e),
                processing_time_ms=int((time.time() - start) * 1000),
            )

        avg_confidence = getattr(ocr_result, "avg_confidence", 0.0)
        full_text = getattr(ocr_result, "full_text", "")

        doc_type = await self._vision.classify_document_type(ocr_result)

        if doc_type == "unreadable" or avg_confidence < 0.30:
            return DocumentProcessingResult(
                document_id=f"doc-{patient_id}",
                document_type=doc_type if doc_type == "unreadable" else "unreadable",
                processing_status="failed",
                error_message="Document is unreadable or image quality too low",
                processing_time_ms=int((time.time() - start) * 1000),
            )

        try:
            structured_data = await self._openai.extract_structured_data(full_text, doc_type)
        except Exception as e:
            return DocumentProcessingResult(
                document_id=f"doc-{patient_id}",
                document_type=doc_type,
                processing_status="failed",
                error_message=str(e),
                processing_time_ms=int((time.time() - start) * 1000),
            )

        try:
            await self._blob.upload_document(image_bytes, f"{patient_id}.{file_extension}")
        except (NotImplementedError, Exception):
            pass

        nodes = []
        confirmation_needed = []
        needs_confirm = False

        medications = structured_data.get("medications", []) if isinstance(structured_data, dict) else []
        for med in medications:
            med_name = med.get("name", "")
            drug_match = self._drug_db.fuzzy_match(med_name)

            conf = ConfidenceCalculator.calculate_medication_confidence(
                source_type="prescription_photo",
                ocr_avg_confidence=avg_confidence,
                drug_match_score=drug_match.confidence,
                dosage_parsed=bool(med.get("dosage")),
                date_found=bool(structured_data.get("date")),
                patient_confirmed=False,
            )

            node = {
                "id": f"node-{med_name.lower().replace(' ', '-')}",
                "node_type": "medication",
                "name": drug_match.generic_name if drug_match.confidence > 0.5 else med_name,
                "confidence": conf.final_score,
            }
            nodes.append(node)

            if conf.final_score < CONFIDENCE_THRESHOLD:
                needs_confirm = True
                confirmation_needed.append(node)

        status = "needs_confirmation" if needs_confirm else "success"

        return DocumentProcessingResult(
            document_id=f"doc-{patient_id}",
            document_type=doc_type,
            processing_status=status,
            nodes_created=nodes,
            interaction_alerts=[],
            care_gap_alerts=[],
            confirmation_needed=confirmation_needed,
            processing_time_ms=int((time.time() - start) * 1000),
        )


document_pipeline = DocumentPipeline()
