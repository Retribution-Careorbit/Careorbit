from services.azure_openai import AzureOpenAIService
from services.azure_vision import AzureVisionService
from services.azure_blob import AzureBlobService
from services.azure_search import AzureSearchService
from services.azure_email import AzureEmailService
from db.session import async_session as db_session
from graph.confidence import ConfidenceCalculator
from graph.orbit_score import OrbitScoreCalculator
from utils.drug_database import DrugDatabase
from pipeline.lab_report_extractor import LabReportExtractor
from pipeline.contracts import validate_extraction_payload

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
        self._lab_extractor = LabReportExtractor()

    def _extract_text_locally(self, image_bytes: bytes, file_extension: str) -> str:
        import io

        ext = (file_extension or "").lower().strip(".")
        if ext == "pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(io.BytesIO(image_bytes))
                page_text = []
                for page in reader.pages:
                    page_text.append(page.extract_text() or "")
                text = "\n".join(page_text).strip()
                if text:
                    return text
            except Exception:
                pass

        # Last-resort decode for simple text-like files mislabeled as PDFs.
        try:
            decoded = image_bytes.decode("utf-8", errors="ignore").strip()
            if decoded:
                return decoded
        except Exception:
            pass
        return ""

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

        # Broader lab parsing for reports where markers are not in the hardcoded list.
        if doc_type in {"lab_report", "medical_document", "unknown"} and text:
            existing = {str(item.get("name", "")).strip().lower() for item in structured["labs"]}
            for parsed in self._lab_extractor.extract(text):
                marker = str(parsed.get("name", "")).strip()
                if not marker or marker.lower() in existing:
                    continue
                raw_value = str(parsed.get("value", "")).replace("<", "").replace(">", "").strip()
                try:
                    value = float(raw_value)
                except ValueError:
                    continue
                structured["labs"].append({
                    "name": marker,
                    "value": value,
                    "unit": parsed.get("unit", ""),
                    "ref_low": None,
                    "ref_high": None,
                })
                existing.add(marker.lower())

        # Handwritten prescription fallback: capture common "name + dose" patterns.
        med_pattern = re.compile(
            r"(?:tab(?:let)?\.?|cap(?:sule)?\.?|syrup|inj(?:ection)?\.?\s*)?"
            r"([A-Za-z][A-Za-z0-9\-]{2,}(?:\s+[A-Za-z][A-Za-z0-9\-]{1,}){0,2})\s+"
            r"(\d{1,4}(?:\.\d+)?\s?(?:mg|mcg|g|ml))",
            re.IGNORECASE,
        )
        existing_meds = {str(item.get("name", "")).strip().lower() for item in structured["medications"]}
        for match in med_pattern.finditer(text or ""):
            name = re.sub(r"\s+", " ", match.group(1)).strip()
            if not name:
                continue
            key = name.lower()
            if key in existing_meds:
                continue
            structured["medications"].append({
                "name": name.title(),
                "dosage": match.group(2).strip(),
                "frequency": "",
            })
            existing_meds.add(key)
            if len(structured["medications"]) >= 8:
                break

        return structured

    def _extract_prescription_context(self, text: str) -> dict:
        import re
        from datetime import datetime

        raw = text or ""
        lower = raw.lower()

        doctor_name = None
        doctor_specialty = None
        follow_up_date = None
        prescribed_on = None
        duration_days = None
        is_ongoing = True

        m_doc = re.search(r"(?:dr\.?\s*)([A-Za-z][A-Za-z .]{2,40})", raw, re.IGNORECASE)
        if m_doc:
            doctor_name = f"Dr. {m_doc.group(1).strip().title()}"

        m_spec = re.search(r"(general physician|endocrinologist|cardiologist|nephrologist|diabetologist)", lower)
        if m_spec:
            doctor_specialty = m_spec.group(1).title()

        m_date = re.search(r"(?:date|prescribed on)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", raw, re.IGNORECASE)
        if m_date:
            parsed = m_date.group(1).replace("-", "/")
            for fmt in ("%d/%m/%Y", "%d/%m/%y"):
                try:
                    prescribed_on = datetime.strptime(parsed, fmt).date().isoformat()
                    break
                except ValueError:
                    continue

        m_follow = re.search(r"(?:follow\s*up|review)\s*(?:on)?\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", raw, re.IGNORECASE)
        if m_follow:
            parsed = m_follow.group(1).replace("-", "/")
            for fmt in ("%d/%m/%Y", "%d/%m/%y"):
                try:
                    follow_up_date = datetime.strptime(parsed, fmt).date().isoformat()
                    break
                except ValueError:
                    continue

        m_days = re.search(r"(?:for\s+)?(\d{1,3})\s*(?:days|day)", lower)
        if m_days:
            duration_days = int(m_days.group(1))

        if any(token in lower for token in ["stopped", "stop", "discontinue", "completed"]):
            is_ongoing = False

        return {
            "doctor_name": doctor_name,
            "doctor_specialty": doctor_specialty,
            "prescribed_on": prescribed_on,
            "follow_up_date": follow_up_date,
            "duration_days": duration_days,
            "is_ongoing": is_ongoing,
        }

    def _extract_conditions(self, structured_data: dict, text: str) -> list[dict]:
        condition_map = {
            "diabetes": ("Type 2 Diabetes Mellitus", "E11.9"),
            "t2dm": ("Type 2 Diabetes Mellitus", "E11.9"),
            "dm": ("Type 2 Diabetes Mellitus", "E11.9"),
            "hypertension": ("Essential Hypertension", "I10"),
            "htn": ("Essential Hypertension", "I10"),
            "dyslipidemia": ("Dyslipidemia", "E78.5"),
            "lipid": ("Dyslipidemia", "E78.5"),
            "ckd": ("Chronic Kidney Disease", "N18.9"),
            "kidney disease": ("Chronic Kidney Disease", "N18.9"),
            "hypothyroid": ("Hypothyroidism", "E03.9"),
            "thyroid": ("Hypothyroidism", "E03.9"),
        }

        discovered: dict[str, dict] = {}

        def add_condition(raw_name: str | None, raw_code: str | None = None, confidence: float = 0.8):
            name = (raw_name or "").strip()
            code = (raw_code or "").strip().upper()
            if not name and not code:
                return

            canonical_name = name
            canonical_code = code or None

            lowered = name.lower()
            for key, mapped in condition_map.items():
                if key in lowered:
                    canonical_name, canonical_code = mapped
                    break

            if canonical_code:
                key = canonical_code
            else:
                key = canonical_name.lower()

            if key not in discovered:
                discovered[key] = {
                    "name": canonical_name,
                    "code": canonical_code,
                    "confidence": confidence,
                    "verified": False,
                }

        diagnoses = structured_data.get("diagnoses") if isinstance(structured_data, dict) else None
        if isinstance(diagnoses, list):
            for item in diagnoses:
                if isinstance(item, dict):
                    add_condition(item.get("name") or item.get("condition"), item.get("code") or item.get("icd10"), 0.84)
                elif isinstance(item, str):
                    add_condition(item, None, 0.8)
        elif isinstance(diagnoses, dict):
            add_condition(diagnoses.get("name") or diagnoses.get("condition"), diagnoses.get("code") or diagnoses.get("icd10"), 0.84)
        elif isinstance(diagnoses, str):
            add_condition(diagnoses, None, 0.8)

        raw_text = (text or "").lower()
        for token, mapped in condition_map.items():
            if token in raw_text:
                add_condition(mapped[0], mapped[1], 0.76)

        return list(discovered.values())

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
        except Exception:
            full_text = ""

        if not (full_text or "").strip():
            local_text = self._extract_text_locally(image_bytes, file_extension)
            if local_text:
                full_text = local_text
                avg_confidence = max(avg_confidence, 0.45)

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
        except Exception:
            structured_data = self._fallback_extract_structured_data(full_text, doc_type)

        if not isinstance(structured_data, dict):
            structured_data = {}

        context = self._extract_prescription_context(full_text)

        # If AI output is sparse, enrich with deterministic fallback extraction.
        ai_meds = structured_data.get("medications", []) if isinstance(structured_data.get("medications"), list) else []
        ai_labs = structured_data.get("labs", []) if isinstance(structured_data.get("labs"), list) else []
        if not ai_meds and not ai_labs:
            fallback_data = self._fallback_extract_structured_data(full_text, doc_type)
            structured_data["medications"] = fallback_data.get("medications", [])
            structured_data["labs"] = fallback_data.get("labs", [])
            if not structured_data.get("summary"):
                structured_data["summary"] = fallback_data.get("summary")

        try:
            await self._blob.upload_document(image_bytes, f"{patient_id}.{file_extension}")
        except (NotImplementedError, Exception):
            pass

        nodes = []
        confirmation_needed = []
        needs_confirm = False

        medications = structured_data.get("medications", []) if isinstance(structured_data, dict) else []
        labs = structured_data.get("labs", []) if isinstance(structured_data, dict) else []
        conditions = self._extract_conditions(structured_data, full_text)

        validated_payload = validate_extraction_payload(
            {
                "medications": medications,
                "labs": labs,
                "conditions": conditions,
            }
        )
        medications = validated_payload.get("medications", [])
        labs = validated_payload.get("labs", [])
        conditions = validated_payload.get("conditions", [])

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
            source_type = "prescription_digital" if file_extension.lower() == "pdf" else "prescription_photo"

            conf = ConfidenceCalculator.calculate_medication_confidence(
                source_type=source_type,
                ocr_avg_confidence=avg_confidence,
                drug_match_score=drug_match.confidence,
                dosage_parsed=bool(med.get("dosage")),
                date_found=bool(context.get("prescribed_on") or structured_data.get("date")),
                patient_confirmed=False,
            )

            resolved_name = drug_match.generic_name if drug_match.confidence > 0.5 else med_name
            prescribed_by = (
                med.get("prescribed_by")
                or med.get("prescribed_by_doctor")
                or context.get("doctor_name")
                or "Uploaded Document"
            )

            node = {
                "id": f"node-{resolved_name.lower().replace(' ', '-')}",
                "node_type": "medication",
                "name": resolved_name,
                "confidence": conf.final_score,
            }
            nodes.append(node)

            med["name"] = resolved_name
            med["confidence"] = conf.final_score
            med["confidence_label"] = conf.confidence_label
            med["rxnorm"] = drug_match.rxnorm_code or med.get("rxnorm")
            med["ner_match"] = bool(drug_match.rxnorm_code)
            med["verified"] = False
            med["source_type"] = source_type
            med["ocr_confidence"] = round(float(avg_confidence or 0.0), 4)
            med["prescribed_by_doctor"] = prescribed_by
            med["doctor_specialty"] = med.get("prescribed_by_specialty") or context.get("doctor_specialty")
            med["prescribed_on"] = med.get("prescribed_on") or context.get("prescribed_on")
            med["duration_days"] = med.get("duration_days") or context.get("duration_days")
            med["is_ongoing"] = med.get("is_ongoing") if med.get("is_ongoing") is not None else context.get("is_ongoing", True)

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

        for condition in conditions:
            cond_name = condition.get("name") or condition.get("code") or "Condition"
            nodes.append(
                {
                    "id": f"node-condition-{str(cond_name).lower().replace(' ', '-')}",
                    "node_type": "condition",
                    "name": cond_name,
                    "confidence": float(condition.get("confidence") or 0.8),
                }
            )

        if len(conditions) == 1:
            cond_code = conditions[0].get("code")
            if cond_code:
                for med in medications:
                    med["condition_code"] = med.get("condition_code") or cond_code
                for lab in labs:
                    lab["condition_code"] = lab.get("condition_code") or cond_code

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
            text_len = len((full_text or "").strip())
            if doc_type in {"prescription", "lab_report", "medicine_strip", "medical_document", "unknown"}:
                inferred_type = "medical_document" if doc_type == "unknown" else doc_type
                summary = "Partial clinical text detected. Please confirm extracted details manually."
                if text_len < 20:
                    summary = "Document received but extraction confidence is low. Please upload a clearer image or confirm details manually."
                return DocumentProcessingResult(
                    document_id=f"doc-{patient_id}",
                    document_type=inferred_type,
                    processing_status="needs_confirmation",
                    nodes_created=[],
                    interaction_alerts=[],
                    care_gap_alerts=[],
                    confirmation_needed=[
                        {
                            "id": f"confirm-{patient_id}",
                            "node_type": "manual_review",
                            "reason": "Low-confidence OCR extraction from uploaded document.",
                        }
                    ],
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
                processing_status="failed",
                nodes_created=[],
                interaction_alerts=[],
                care_gap_alerts=[],
                confirmation_needed=[],
                processing_time_ms=int((time.time() - start) * 1000),
                error_message="Could not extract clinical data. Please upload a clearer prescription or lab report.",
                extracted_data={"medications": [], "labs": []},
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
                "conditions": conditions,
                "summary": structured_data.get("summary") if isinstance(structured_data, dict) else None,
                "context": context,
                "quality": {
                    "source_type": "prescription_digital" if file_extension.lower() == "pdf" else "prescription_photo",
                    "ocr_confidence": round(float(avg_confidence or 0.0), 4),
                },
            },
        )


document_pipeline = DocumentPipeline()
