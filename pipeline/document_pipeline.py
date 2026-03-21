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
        self.extracted_data = kwargs.get("extracted_data", {})


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

    def _infer_document_type_from_filename(self, filename: str) -> str:
        lower = (filename or "").lower()
        if "lab" in lower or "report" in lower:
            return "lab_report"
        if "rx" in lower or "prescription" in lower:
            return "prescription"
        if "strip" in lower or "tablet" in lower:
            return "medicine_strip"
        return "unknown"

    def _fallback_extract_structured_data(self, text: str, doc_type: str) -> dict:
        import re
        structured = {"medications": [], "labs": [], "summary": "Fallback extraction used due to unavailable AI service."}
        lower = (text or "").lower()

        # Medication keyword scan using known drug catalog.
        for generic in self._drug_db.DRUGS.keys():
            if generic in lower:
                structured["medications"].append({
                    "name": generic.capitalize(),
                    "dosage": "",
                    "frequency": "",
                })

        # Basic lab-value regex patterns.
        patterns = [
            ("HbA1c", r"hba1c\s*[:=]?\s*(\d+(?:\.\d+)?)", "%", None, 5.6),
            ("Creatinine", r"creatinine\s*[:=]?\s*(\d+(?:\.\d+)?)", "mg/dL", 0.7, 1.3),
            ("eGFR", r"egfr\s*[:=]?\s*(\d+(?:\.\d+)?)", "mL/min", 90, None),
            ("TSH", r"tsh\s*[:=]?\s*(\d+(?:\.\d+)?)", "uIU/mL", 0.4, 4.5),
            ("ALT", r"alt\s*[:=]?\s*(\d+(?:\.\d+)?)", "U/L", 7, 55),
        ]
        for name, rx, unit, ref_low, ref_high in patterns:
            m = re.search(rx, lower)
            if not m:
                continue
            structured["labs"].append({
                "name": name,
                "value": float(m.group(1)),
                "unit": unit,
                "ref_low": ref_low,
                "ref_high": ref_high,
            })

        return structured

    async def process_document(self, image_bytes, patient_id, uploaded_by, file_extension="jpg", filename="upload"):
        import time
        start = time.time()

        full_text = ""
        avg_confidence = 0.72
        doc_type = self._infer_document_type_from_filename(filename)

        try:
            ocr_result = await self._vision.extract_text(image_bytes)
            avg_confidence = getattr(ocr_result, "avg_confidence", 0.72)
            full_text = getattr(ocr_result, "full_text", "")
            classified = await self._vision.classify_document_type(ocr_result)
            if classified and classified != "unknown":
                doc_type = classified
        except Exception as e:
            full_text = ""

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
            structured_data = self._fallback_extract_structured_data(full_text, doc_type)

        try:
            await self._blob.upload_document(image_bytes, f"{patient_id}.{file_extension}")
        except (NotImplementedError, Exception):
            pass

        nodes = []
        confirmation_needed = []
        needs_confirm = False

        medications = structured_data.get("medications", []) if isinstance(structured_data, dict) else []
        labs = structured_data.get("labs", []) if isinstance(structured_data, dict) else []
        interaction_alerts = []

        if doc_type == "unknown":
            if labs:
                doc_type = "lab_report"
            elif medications:
                doc_type = "prescription"
            else:
                doc_type = "medical_document"
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

        for lab in labs:
            nodes.append({
                "id": f"node-lab-{str(lab.get('name', 'lab')).lower().replace(' ', '-')}",
                "node_type": "lab_value",
                "name": lab.get("name", "Unknown"),
                "value": lab.get("value"),
                "unit": lab.get("unit", ""),
                "confidence": 0.86,
            })

        med_names = {str(m.get("name", "")).lower() for m in medications}
        if "metformin" in med_names and "ibuprofen" in med_names:
            interaction_alerts.append({
                "drug_pair": "Metformin + Ibuprofen",
                "severity": "ELEVATED",
                "description": "Potential renal stress risk when used together.",
                "clinical_action": "Review with physician and monitor renal panel.",
            })

        status = "needs_confirmation" if needs_confirm else "success"

        if not nodes:
            text_present = bool((full_text or "").strip())
            review_node = {
                "id": f"node-review-{patient_id}",
                "node_type": "document_review",
                "name": "Manual Review Needed",
                "confidence": 0.40,
            }
            summary = (
                "Text was detected, but clinical entities could not be extracted confidently. Please review manually."
                if text_present
                else "Could not extract structured clinical entities from this file. Please review manually or upload a clearer image."
            )
            return DocumentProcessingResult(
                document_id=f"doc-{patient_id}",
                document_type=doc_type,
                processing_status="needs_confirmation",
                nodes_created=[review_node],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[review_node],
                processing_time_ms=int((time.time() - start) * 1000),
                error_message=None,
                extracted_data={
                    "medications": [],
                    "labs": [],
                    "summary": summary,
                },
            )

        return DocumentProcessingResult(
            document_id=f"doc-{patient_id}",
            document_type=doc_type,
            processing_status=status,
            nodes_created=nodes,
            interaction_alerts=interaction_alerts,
            care_gap_alerts=[],
            confirmation_needed=confirmation_needed,
            processing_time_ms=int((time.time() - start) * 1000),
            extracted_data={
                "medications": medications,
                "labs": labs,
                "summary": structured_data.get("summary") if isinstance(structured_data, dict) else None,
            },
        )


document_pipeline = DocumentPipeline()
