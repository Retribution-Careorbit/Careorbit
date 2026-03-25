from services.azure_openai import AzureOpenAIService
from services.azure_vision import AzureVisionService
from services.azure_language import AzureLanguageService
from services.azure_blob import AzureBlobService
from services.azure_search import AzureSearchService
from services.azure_email import AzureEmailService
from config import get_settings
from db.session import async_session as db_session
from graph.confidence import ConfidenceCalculator
from graph.orbit_score import OrbitScoreCalculator
from pipeline.validation_gate import validation_gate
from utils.drug_database import DrugDatabase

openai_service = AzureOpenAIService()
vision_service = AzureVisionService()
language_service = AzureLanguageService()
blob_service = AzureBlobService()
search_service = AzureSearchService()
email_service = AzureEmailService()

CONFIDENCE_THRESHOLD = 0.70
LOW_CONFIDENCE_REVIEW_THRESHOLD = 0.60


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
        self._settings = get_settings()
        self._vision = mod.vision_service
        self._language = mod.language_service
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
        structured = {
            "doctor_name": self._extract_doctor_name(text),
            "medications": [],
            "labs": [],
            "summary": "Fallback extraction used due to unavailable AI service.",
        }
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

    def _extract_doctor_name(self, text: str) -> str:
        import re
        if not text:
            return ""
        for line in text.splitlines():
            line_clean = line.strip()
            if not line_clean:
                continue
            # Capture common doctor prefixes from OCR text, e.g. Dr. A. Sharma
            if re.search(r"\bdr\.?\b", line_clean, flags=re.IGNORECASE):
                return line_clean
        return ""

    async def process_document(self, image_bytes, patient_id, uploaded_by, file_extension="jpg", filename="upload"):
        import time
        start = time.time()

        full_text = ""
        avg_confidence = 0.72
        doc_type = self._infer_document_type_from_filename(filename)
        blob_url = None

        # Step 1: persist raw document to Blob first so downstream processing is retryable.
        try:
            blob_url = await self._blob.upload_document(
                image_bytes,
                filename,
                document_type=doc_type,
                patient_id=patient_id,
            )
        except (NotImplementedError, Exception):
            environment = str(getattr(self._settings, "ENVIRONMENT", "development") or "development").strip().lower()
            strict_blob_required = bool(self._settings.DOCUMENTS_REQUIRE_BLOB_DURABILITY) and environment in {"production", "prod"}
            if strict_blob_required:
                return DocumentProcessingResult(
                    document_id=f"doc-{patient_id}",
                    document_type=doc_type,
                    processing_status="failed",
                    error_message="Durable blob storage upload failed. Please retry upload.",
                    processing_time_ms=int((time.time() - start) * 1000),
                    extracted_data={"source_blob_url": None},
                )
            # Non-production: continue with in-memory bytes using controlled degraded mode.
            blob_url = None

        try:
            ocr_result = await self._vision.extract_text(image_bytes, blob_url=blob_url)
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

        clinical_entities = []
        try:
            clinical_entities = await self._language.recognize_health_entities(full_text)
        except Exception:
            clinical_entities = []

        med_entities = {
            str(ent.get("text") or "").strip().lower()
            for ent in clinical_entities
            if str(ent.get("category") or "").lower() in {"medicationname", "medication"}
            and str(ent.get("text") or "").strip()
        }

        lab_entities = {
            str(ent.get("text") or "").strip().lower()
            for ent in clinical_entities
            if str(ent.get("text") or "").strip()
            and (
                "lab" in str(ent.get("category") or "").lower()
                or "measurement" in str(ent.get("category") or "").lower()
                or "test" in str(ent.get("category") or "").lower()
            )
        }

        nodes = []
        confirmation_needed = []
        needs_confirm = False

        medications = structured_data.get("medications", []) if isinstance(structured_data, dict) else []
        labs = []
        if isinstance(structured_data, dict):
            labs = structured_data.get("lab_results") or structured_data.get("labs") or []
        interaction_alerts = []

        if doc_type == "unknown":
            if labs:
                doc_type = "lab_report"
            elif medications:
                doc_type = "prescription"
            else:
                doc_type = "medical_document"
        medication_confidences = []
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
                ner_match=med_name.strip().lower() in med_entities,
            )

            node = {
                "id": f"node-{med_name.lower().replace(' ', '-')}",
                "node_type": "medication",
                "name": drug_match.generic_name if drug_match.confidence > 0.5 else med_name,
                "confidence": conf.final_score,
            }
            nodes.append(node)
            medication_confidences.append(conf.final_score)

            if conf.final_score < CONFIDENCE_THRESHOLD:
                needs_confirm = True
                confirmation_needed.append(node)

        text_anchor_names = {
            str(lab.get("name") or "").strip().lower()
            for lab in labs
            if str(lab.get("name") or "").strip()
            and str(lab.get("name") or "").strip().lower() in (full_text or "").lower()
        }

        normalized_labs = []
        rejected_labs = []
        for lab in labs:
            lab_name = str(lab.get("name") or "").strip()
            if not lab_name:
                continue

            gate_decision = await validation_gate.validate_lab_result(
                patient_id=patient_id,
                lab_result=lab,
                ner_names=lab_entities,
                text_anchor_names=text_anchor_names,
            )
            if not gate_decision.accepted:
                rejected_labs.append(
                    {
                        "name": lab_name,
                        "value": lab.get("value"),
                        "unit": lab.get("unit"),
                        "reasons": gate_decision.reasons,
                        "agreement_count": gate_decision.agreement_count,
                    }
                )
                continue

            lab_conf = ConfidenceCalculator.calculate_lab_confidence(
                source_type="lab_report_photo",
                ocr_avg_confidence=avg_confidence,
                value_parsed=lab.get("value") is not None,
                unit_recognized=bool(str(lab.get("unit") or "").strip()),
                reference_range_found=bool(lab.get("ref_low") is not None or lab.get("ref_high") is not None),
                patient_confirmed=False,
                ner_match=lab_name.lower() in lab_entities,
            )

            nodes.append({
                "id": f"node-lab-{lab_name.lower().replace(' ', '-')}",
                "node_type": "lab_value",
                "name": lab_name,
                "value": lab.get("value"),
                "unit": lab.get("unit", ""),
                "confidence": lab_conf.final_score,
            })
            normalized_labs.append(
                {
                    "name": lab_name,
                    "value": lab.get("value"),
                    "unit": lab.get("unit", ""),
                    "ref_low": lab.get("ref_low"),
                    "ref_high": lab.get("ref_high"),
                    "loinc": lab.get("loinc"),
                    "confidence": lab_conf.final_score,
                    "confidence_label": lab_conf.confidence_label,
                }
            )

        for med in medications:
            med_name = str(med.get("name") or "").strip()
            if not med_name:
                continue
            try:
                interactions = await self._search.search_drug_interactions(med_name)
                if isinstance(interactions, list) and interactions:
                    interaction_alerts.extend(interactions[:3])
            except Exception:
                # Search may be unavailable locally; keep extraction flow running.
                continue

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
                    "lab_rejections": rejected_labs,
                    "source_blob_url": blob_url,
                    "summary": summary,
                },
            )

        doctor_name = ""
        if isinstance(structured_data, dict):
            doctor_name = str(structured_data.get("doctor_name") or "").strip()
            if not doctor_name:
                doctor_name = self._extract_doctor_name(full_text)

        coding_by_text = {}
        for ent in clinical_entities:
            text_key = str(ent.get("text") or "").strip().lower()
            if not text_key:
                continue
            if str(ent.get("category") or "").lower() in {"medicationname", "medication"}:
                coding_by_text[text_key] = ent.get("coding", [])

        normalized_medications = []
        for idx, med in enumerate(medications):
            med_name = (med.get("name") or "").strip()
            normalized_medications.append({
                "name": med_name,
                "dosage": (med.get("dosage") or "").strip(),
                "frequency": (med.get("frequency") or "").strip(),
                "dose_to_take": (med.get("dose_to_take") or med.get("dosage") or "").strip(),
                "coding": coding_by_text.get(med_name.lower(), []),
                "confidence": medication_confidences[idx] if idx < len(medication_confidences) else 0.0,
            })

        missing_fields = []
        low_confidence_fields = []
        if doc_type == "lab_report":
            if not normalized_labs:
                missing_fields.append("labs")
        else:
            if not doctor_name:
                missing_fields.append("doctor_name")
            doctor_conf_raw = structured_data.get("doctor_name_confidence") if isinstance(structured_data, dict) else None
            try:
                doctor_conf = float(doctor_conf_raw) if doctor_conf_raw is not None else None
            except (TypeError, ValueError):
                doctor_conf = None
            if doctor_name and doctor_conf is not None and doctor_conf < LOW_CONFIDENCE_REVIEW_THRESHOLD:
                low_confidence_fields.append("doctor_name")
            if not normalized_medications:
                missing_fields.append("medications")
            else:
                for i, med in enumerate(normalized_medications):
                    if not med.get("name"):
                        missing_fields.append(f"medications[{i}].name")
                    if not med.get("dosage"):
                        missing_fields.append(f"medications[{i}].dosage")
                    med_conf = med.get("confidence")
                    if isinstance(med_conf, (float, int)) and float(med_conf) < LOW_CONFIDENCE_REVIEW_THRESHOLD:
                        low_confidence_fields.append(f"medications[{i}].name")
                        low_confidence_fields.append(f"medications[{i}].dosage")

        if missing_fields or low_confidence_fields:
            needs_confirm = True
            status = "needs_confirmation"

        if rejected_labs and not normalized_labs and doc_type == "lab_report":
            needs_confirm = True
            status = "needs_confirmation"

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
                "doctor_name": doctor_name,
                "medications": normalized_medications,
                "labs": normalized_labs,
                "lab_rejections": rejected_labs,
                "summary": structured_data.get("summary") if isinstance(structured_data, dict) else None,
                "missing_fields": missing_fields,
                "low_confidence_fields": low_confidence_fields,
                "clinical_entities": clinical_entities,
                "source_blob_url": blob_url,
            },
        )


document_pipeline = DocumentPipeline()
