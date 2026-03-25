from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import StreamingResponse
import io
import logging
import json
import re
from datetime import datetime, timezone
from uuid import uuid4
from uuid import UUID
from pydantic import BaseModel, Field
from config import get_settings

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.seed_demo import DEMO_USER_ID, RAMESH_UPLOADED_DOCUMENTS
from pipeline.document_pipeline import document_pipeline
from services.azure_language import AzureLanguageService
from services.azure_openai import AzureOpenAIService
from graph.phig_builder import phig_builder
from graph.confidence import ConfidenceCalculator
from graph.phig_integrity import phig_integrity
from pipeline.validation_gate import validation_gate
from utils.pdf_generator import generate_uploaded_document_pdf
from db.session import async_session
from db.runtime_store import (
    get_patient_documents,
    add_patient_document,
    update_patient_document,
    get_valid_lab_reports,
    add_extracted_medications,
    save_pending_document_review,
    get_pending_document_review,
    remove_pending_document_review,
    push_notification,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = logging.getLogger("careorbit.routes.documents")

language_service = AzureLanguageService()
openai_service = AzureOpenAIService()

_BASE_ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic"]
MAX_SIZE = 10 * 1024 * 1024


class MedicationReviewItem(BaseModel):
    name: str = ""
    dosage: str = ""
    frequency: str = ""
    dose_to_take: str = ""


class ConfirmExtractionRequest(BaseModel):
    doctor_name: str = ""
    medications: list[MedicationReviewItem] = Field(default_factory=list)


def _extract_json_object(text: str) -> dict | None:
    if not text:
        return None
    candidate = text.strip()
    try:
        return json.loads(candidate)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", candidate)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _build_confirmation_text(doctor_name: str, medications: list[dict]) -> str:
    lines = [f"Doctor: {doctor_name}", "Confirmed medications:"]
    for med in medications:
        lines.append(
            f"- {med.get('name', '')}; dosage={med.get('dosage', '')}; "
            f"frequency={med.get('frequency', '')}; dose_to_take={med.get('dose_to_take', '')}"
        )
    return "\n".join(lines)


def _normalize_uuid(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError):
        return None


async def _persist_document_to_db(
    patient_id: str,
    document_id: str,
    document_type: str,
    file_url: str,
    original_filename: str,
    content_type: str,
    file_size_bytes: int,
    processing_status: str,
    structured_data: dict,
    ocr_text: str = "",
    ocr_confidence: float = 0.0,
    error_message: str | None = None,
    processing_time_ms: int | None = None,
) -> bool:
    normalized_patient_id = _normalize_uuid(patient_id)
    normalized_document_id = _normalize_uuid(document_id)
    if not normalized_patient_id or not normalized_document_id:
        return False

    try:
        async with async_session() as session:
            existing = await session.execute(
                "SELECT id FROM documents WHERE id = :doc_id",
                {"doc_id": normalized_document_id},
            )
            existing_row = existing.mappings().first()

            params = {
                "doc_id": normalized_document_id,
                "patient_id": normalized_patient_id,
                "document_type": document_type,
                "file_url": file_url,
                "original_filename": original_filename,
                "content_type": content_type,
                "file_size_bytes": file_size_bytes,
                "ocr_text": ocr_text,
                "ocr_confidence": ocr_confidence,
                "structured_data": json.dumps(structured_data or {}),
                "processing_status": processing_status,
                "error_message": error_message,
                "processing_time_ms": processing_time_ms,
            }

            if existing_row:
                await session.execute(
                    "UPDATE documents SET "
                    "document_type = CAST(:document_type AS document_type), "
                    "file_url = :file_url, "
                    "original_filename = :original_filename, "
                    "content_type = :content_type, "
                    "file_size_bytes = :file_size_bytes, "
                    "ocr_text = :ocr_text, "
                    "ocr_confidence = :ocr_confidence, "
                    "structured_data = CAST(:structured_data AS JSONB), "
                    "processing_status = CAST(:processing_status AS document_status), "
                    "error_message = :error_message, "
                    "processing_time_ms = :processing_time_ms, "
                    "updated_at = NOW() "
                    "WHERE id = :doc_id",
                    params,
                )
            else:
                await session.execute(
                    "INSERT INTO documents ("
                    "id, patient_id, document_type, file_url, original_filename, content_type, "
                    "file_size_bytes, ocr_text, ocr_confidence, structured_data, processing_status, "
                    "error_message, processing_time_ms"
                    ") VALUES ("
                    ":doc_id, :patient_id, CAST(:document_type AS document_type), :file_url, :original_filename, :content_type, "
                    ":file_size_bytes, :ocr_text, :ocr_confidence, CAST(:structured_data AS JSONB), CAST(:processing_status AS document_status), "
                    ":error_message, :processing_time_ms"
                    ")",
                    params,
                )

            await session.commit()
            return True
    except Exception:
        logger.exception("Failed to persist document row patient_id=%s document_id=%s", patient_id, document_id)
        return False


def _extract_peer_medication_name(drug_pair: str, source_name: str) -> str | None:
    parts = [part.strip() for part in (drug_pair or "").split("+") if part.strip()]
    if len(parts) < 2:
        return None
    source_lower = source_name.strip().lower()
    for part in parts:
        if part.lower() != source_lower:
            return part
    return None


async def _persist_medications_to_phig_db(patient_id: str, document_id: str, medications: list[dict]) -> tuple[bool, int]:
    normalized_patient_id = _normalize_uuid(patient_id)
    normalized_document_id = _normalize_uuid(document_id)
    if not normalized_patient_id:
        return False, 0

    persisted = 0

    try:
        async with async_session() as session:
            existing_nodes_result = await session.execute(
                "SELECT id, display_name FROM phig_nodes "
                "WHERE patient_id = :pid AND node_type = CAST('medication' AS node_type) AND is_active = TRUE",
                {"pid": normalized_patient_id},
            )
            existing_nodes = existing_nodes_result.mappings().all()
            node_ids_by_name = {
                str(row.get("display_name") or "").strip().lower(): str(row.get("id"))
                for row in existing_nodes
                if row.get("display_name")
            }

            for med in medications:
                med_name = str(med.get("name") or "").strip()
                if not med_name:
                    continue

                node_id = node_ids_by_name.get(med_name.lower())
                node_params = {
                    "pid": normalized_patient_id,
                    "doc_id": normalized_document_id,
                    "display_name": med_name,
                    "dosage": str(med.get("dosage") or "").strip() or None,
                    "frequency": str(med.get("frequency") or "").strip() or None,
                    "rxnorm": str(med.get("rxnorm") or "").strip() or None,
                    "confidence": float(med.get("confidence") or 0.92),
                    "metadata": json.dumps(
                        {
                            "prescribed_by_doctor": med.get("prescribed_by_doctor"),
                            "dose_to_take": med.get("dose_to_take"),
                            "confidence_label": med.get("confidence_label"),
                            "validation_status": med.get("validation_status"),
                            "validation_notes": med.get("validation_notes"),
                            "coding": med.get("coding") or [],
                            "interactions": med.get("interactions") or [],
                        }
                    ),
                }

                if node_id:
                    node_params["node_id"] = node_id
                    await session.execute(
                        "UPDATE phig_nodes SET "
                        "document_id = COALESCE(:doc_id, document_id), "
                        "display_name = :display_name, "
                        "dosage = :dosage, "
                        "frequency = :frequency, "
                        "rxnorm_code = :rxnorm, "
                        "confidence_score = :confidence, "
                        "confidence_source = 'patient_confirmed', "
                        "metadata = CAST(:metadata AS JSONB), "
                        "is_active = TRUE, "
                        "updated_at = NOW() "
                        "WHERE id = :node_id",
                        node_params,
                    )
                else:
                    created = await session.execute(
                        "INSERT INTO phig_nodes ("
                        "patient_id, document_id, node_type, display_name, dosage, frequency, rxnorm_code, "
                        "confidence_score, confidence_source, metadata"
                        ") VALUES ("
                        ":pid, :doc_id, CAST('medication' AS node_type), :display_name, :dosage, :frequency, :rxnorm, "
                        ":confidence, 'patient_confirmed', CAST(:metadata AS JSONB)"
                        ") RETURNING id",
                        node_params,
                    )
                    created_row = created.mappings().first()
                    node_id = str((created_row or {}).get("id") or "")
                    if node_id:
                        node_ids_by_name[med_name.lower()] = node_id

                if node_id:
                    persisted += 1

            for med in medications:
                source_name = str(med.get("name") or "").strip()
                source_node_id = node_ids_by_name.get(source_name.lower())
                if not source_node_id:
                    continue

                for interaction in med.get("interactions") or []:
                    if not isinstance(interaction, dict):
                        continue
                    peer_name = _extract_peer_medication_name(
                        str(interaction.get("drug_pair") or ""),
                        source_name,
                    )
                    if not peer_name:
                        continue

                    target_node_id = node_ids_by_name.get(peer_name.lower())
                    if not target_node_id or target_node_id == source_node_id:
                        continue

                    exists = await session.execute(
                        "SELECT id FROM phig_edges "
                        "WHERE patient_id = :pid AND source_node_id = :src AND target_node_id = :dst "
                        "AND edge_type = 'interaction' AND is_active = TRUE "
                        "LIMIT 1",
                        {
                            "pid": normalized_patient_id,
                            "src": source_node_id,
                            "dst": target_node_id,
                        },
                    )
                    if exists.mappings().first():
                        continue

                    await session.execute(
                        "INSERT INTO phig_edges ("
                        "patient_id, source_node_id, target_node_id, edge_type, severity, description, clinical_action, metadata"
                        ") VALUES ("
                        ":pid, :src, :dst, 'interaction', :severity, :description, :clinical_action, CAST(:metadata AS JSONB)"
                        ")",
                        {
                            "pid": normalized_patient_id,
                            "src": source_node_id,
                            "dst": target_node_id,
                            "severity": str(interaction.get("severity") or "unknown")[:20],
                            "description": str(interaction.get("description") or ""),
                            "clinical_action": str(interaction.get("clinical_action") or ""),
                            "metadata": json.dumps(interaction),
                        },
                    )

            await session.commit()
            return True, persisted
    except Exception:
        try:
            async with async_session() as rollback_session:
                await rollback_session.rollback()
        except Exception:
            pass
        logger.exception("Failed to persist PHIG medications patient_id=%s document_id=%s", patient_id, document_id)
        return False, 0


async def _persist_labs_to_phig_db(
    patient_id: str,
    document_id: str,
    labs: list[dict],
    clinical_entities: list[dict] | None = None,
) -> tuple[bool, int, list[dict]]:
    normalized_patient_id = _normalize_uuid(patient_id)
    normalized_document_id = _normalize_uuid(document_id)
    if not normalized_patient_id:
        return False, 0, []

    clinical_entities = clinical_entities or []
    rejected: list[dict] = []
    persisted = 0

    ner_names = {
        str(ent.get("text") or "").strip().lower()
        for ent in clinical_entities
        if str(ent.get("text") or "").strip()
    }
    text_anchor_names = {
        str(lab.get("name") or "").strip().lower()
        for lab in labs
        if str(lab.get("name") or "").strip()
    }

    try:
        async with async_session() as session:
            existing_nodes_result = await session.execute(
                "SELECT id, display_name FROM phig_nodes "
                "WHERE patient_id = :pid AND node_type = CAST('lab_result' AS node_type) AND is_active = TRUE",
                {"pid": normalized_patient_id},
            )
            existing_nodes = existing_nodes_result.mappings().all()
            node_ids_by_name = {
                str(row.get("display_name") or "").strip().lower(): str(row.get("id"))
                for row in existing_nodes
                if row.get("display_name")
            }

            for lab in labs:
                lab_name = str(lab.get("name") or "").strip()
                if not lab_name:
                    continue

                gate_decision = await validation_gate.validate_lab_result(
                    patient_id=patient_id,
                    lab_result=lab,
                    ner_names=ner_names,
                    text_anchor_names=text_anchor_names,
                )
                if not gate_decision.accepted:
                    rejected.append(
                        {
                            "name": lab_name,
                            "value": lab.get("value"),
                            "unit": lab.get("unit"),
                            "reasons": gate_decision.reasons,
                            "agreement_count": gate_decision.agreement_count,
                        }
                    )
                    continue

                confidence = float(lab.get("confidence") or 0.85)
                metadata = {
                    "confidence_label": lab.get("confidence_label") or "MODERATE",
                }

                node_params = {
                    "pid": normalized_patient_id,
                    "doc_id": normalized_document_id,
                    "display_name": lab_name,
                    "loinc": str(lab.get("loinc") or "").strip() or None,
                    "value": float(lab.get("value")) if lab.get("value") is not None else None,
                    "unit": str(lab.get("unit") or "").strip() or None,
                    "ref_low": float(lab.get("ref_low")) if lab.get("ref_low") is not None else None,
                    "ref_high": float(lab.get("ref_high")) if lab.get("ref_high") is not None else None,
                    "abnormal": bool(lab.get("abnormal")) if lab.get("abnormal") is not None else None,
                    "confidence": confidence,
                    "metadata": json.dumps(metadata),
                }

                node_id = node_ids_by_name.get(lab_name.lower())
                if node_id:
                    node_params["node_id"] = node_id
                    await session.execute(
                        "UPDATE phig_nodes SET "
                        "document_id = COALESCE(:doc_id, document_id), "
                        "display_name = :display_name, "
                        "loinc_code = :loinc, "
                        "value = :value, "
                        "unit = :unit, "
                        "reference_range_low = :ref_low, "
                        "reference_range_high = :ref_high, "
                        "is_abnormal = :abnormal, "
                        "confidence_score = :confidence, "
                        "confidence_source = 'document_pipeline', "
                        "metadata = CAST(:metadata AS JSONB), "
                        "is_active = TRUE, "
                        "updated_at = NOW() "
                        "WHERE id = :node_id",
                        node_params,
                    )
                else:
                    created = await session.execute(
                        "INSERT INTO phig_nodes ("
                        "patient_id, document_id, node_type, display_name, loinc_code, value, unit, "
                        "reference_range_low, reference_range_high, is_abnormal, confidence_score, confidence_source, metadata"
                        ") VALUES ("
                        ":pid, :doc_id, CAST('lab_result' AS node_type), :display_name, :loinc, :value, :unit, "
                        ":ref_low, :ref_high, :abnormal, :confidence, 'document_pipeline', CAST(:metadata AS JSONB)"
                        ") RETURNING id",
                        node_params,
                    )
                    created_row = created.mappings().first()
                    node_id = str((created_row or {}).get("id") or "")
                    if node_id:
                        node_ids_by_name[lab_name.lower()] = node_id

                if node_id:
                    persisted += 1

            await session.commit()
            return True, persisted, rejected
    except Exception:
        try:
            async with async_session() as rollback_session:
                await rollback_session.rollback()
        except Exception:
            pass
        logger.exception("Failed to persist PHIG labs patient_id=%s document_id=%s", patient_id, document_id)
        return False, 0, rejected


async def _post_confirmation_pipeline(patient_id: str, doctor_name: str, reviewed_meds: list[dict]) -> tuple[list[dict], dict, list[str]]:
    pipeline_trace = {
        "language_ner": "skipped",
        "gpt_orchestrator": "skipped",
        "validation": "pending",
        "phig_write": "pending",
    }
    warnings: list[str] = []
    clinical_text = _build_confirmation_text(doctor_name, reviewed_meds)

    entities: list[dict] = []
    try:
        entities = await language_service.recognize_health_entities(clinical_text)
        pipeline_trace["language_ner"] = "ok"
    except Exception as exc:
        pipeline_trace["language_ner"] = "fallback"
        warnings.append(f"Language NER unavailable: {exc}")

    orchestrated_meds = reviewed_meds
    try:
        orchestrator_prompt = {
            "doctor_name": doctor_name,
            "medications": reviewed_meds,
            "language_entities": entities,
            "task": "Validate and normalize confirmed medication data for PHIG insertion",
        }
        response = await openai_service.chat([
            {
                "role": "system",
                "content": (
                    "You are a medical data orchestrator. "
                    "Return strict JSON with keys doctor_name, medications, validation_summary. "
                    "For each medication return: name, dosage, frequency, dose_to_take, validation_status, validation_notes."
                ),
            },
            {"role": "user", "content": json.dumps(orchestrator_prompt)},
        ])

        parsed = _extract_json_object(response if isinstance(response, str) else str(response))
        parsed_meds = (parsed or {}).get("medications", []) if isinstance(parsed, dict) else []
        if isinstance(parsed_meds, list) and parsed_meds:
            normalized = []
            for med in parsed_meds:
                if not isinstance(med, dict):
                    continue
                normalized.append(
                    {
                        "name": str(med.get("name") or "").strip(),
                        "dosage": str(med.get("dosage") or "").strip(),
                        "frequency": str(med.get("frequency") or "").strip(),
                        "dose_to_take": str(med.get("dose_to_take") or med.get("dosage") or "").strip(),
                        "validation_status": str(med.get("validation_status") or "confirmed").strip(),
                        "validation_notes": str(med.get("validation_notes") or "").strip(),
                    }
                )
            if normalized:
                orchestrated_meds = normalized
                pipeline_trace["gpt_orchestrator"] = "ok"
            else:
                pipeline_trace["gpt_orchestrator"] = "fallback"
                warnings.append("GPT orchestration returned no usable medications; using confirmed input.")
        else:
            pipeline_trace["gpt_orchestrator"] = "fallback"
            warnings.append("GPT orchestration returned non-parseable output; using confirmed input.")
    except Exception as exc:
        pipeline_trace["gpt_orchestrator"] = "fallback"
        warnings.append(f"GPT orchestrator unavailable: {exc}")

    coding_by_text: dict[str, list[dict]] = {}
    for ent in entities:
        text_key = str(ent.get("text") or "").strip().lower()
        if text_key:
            coding_by_text[text_key] = ent.get("coding", []) or []

    validated: list[dict] = []
    rejected: list[dict] = []
    validation_errors: list[str] = []
    user_confirmed_names = {
        str(item.get("name") or "").strip().lower()
        for item in reviewed_meds
        if str(item.get("name") or "").strip()
    }
    ner_names = {
        str(ent.get("text") or "").strip().lower()
        for ent in entities
        if str(ent.get("text") or "").strip()
    }

    for i, med in enumerate(orchestrated_meds):
        name = str(med.get("name") or "").strip()
        dosage = str(med.get("dosage") or "").strip()
        if not name:
            validation_errors.append(f"medications[{i}].name")
            continue
        if not dosage:
            validation_errors.append(f"medications[{i}].dosage")
            continue

        interactions = []
        try:
            interactions = await phig_builder.check_interactions_for_node(patient_id, name)
        except Exception as exc:
            warnings.append(f"Interaction check failed for {name}: {exc}")

        candidate = {
            "name": name,
            "dosage": dosage,
            "frequency": str(med.get("frequency") or "").strip(),
            "dose_to_take": str(med.get("dose_to_take") or dosage).strip(),
            "prescribed_by_doctor": doctor_name,
            "confidence": ConfidenceCalculator.calculate_medication_confidence(
                source_type="patient_confirmed",
                ocr_avg_confidence=1.0,
                drug_match_score=1.0,
                dosage_parsed=bool(dosage),
                date_found=False,
                patient_confirmed=True,
                ner_match=bool(coding_by_text.get(name.lower(), [])),
            ).final_score,
            "confidence_label": "VALIDATED",
            "validation_status": str(med.get("validation_status") or "confirmed").strip(),
            "validation_notes": str(med.get("validation_notes") or "").strip(),
            "coding": coding_by_text.get(name.lower(), []),
            "interactions": interactions if isinstance(interactions, list) else [],
        }

        gate_decision = await validation_gate.validate_medication(
            patient_id=patient_id,
            medication=candidate,
            user_confirmed_names=user_confirmed_names,
            ner_names=ner_names,
        )
        if gate_decision.accepted:
            validated.append(candidate)
        else:
            rejected.append(
                {
                    "name": name,
                    "reasons": gate_decision.reasons,
                    "agreement_count": gate_decision.agreement_count,
                }
            )

    if validation_errors:
        pipeline_trace["validation"] = "failed"
        raise HTTPException(
            status_code=422,
            detail={
                "error": "post_confirmation_validation_failed",
                "missing_fields": validation_errors,
                "pipeline_trace": pipeline_trace,
            },
        )

    if rejected:
        warnings.append(f"Validation gate rejected {len(rejected)} medication(s): {json.dumps(rejected)}")

    if not validated:
        pipeline_trace["validation"] = "failed"
        raise HTTPException(
            status_code=422,
            detail={
                "error": "post_confirmation_validation_gate_failed",
                "rejections": rejected,
                "pipeline_trace": pipeline_trace,
            },
        )

    pipeline_trace["validation"] = "ok"
    return validated, pipeline_trace, warnings


@router.post("/upload")
async def upload_document(
    request: Request,
    file: UploadFile = File(None),
):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])

    await rbac_mod.verify_patient_access(current_user["id"], patient_id, "edit")

    if file is None:
        raise HTTPException(status_code=422, detail="File field is required")

    settings = get_settings()
    allowed_types = list(_BASE_ALLOWED_TYPES)
    if settings.DOCUMENTS_ALLOW_PDF_UPLOADS:
        allowed_types.append("application/pdf")

    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed. Allowed: {allowed_types}")

    contents = await file.read()

    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"

    try:
        result = await document_pipeline.process_document(
            image_bytes=contents,
            patient_id=patient_id,
            uploaded_by=current_user["id"],
            file_extension=ext,
            filename=file.filename or "upload",
        )
    except NotImplementedError:
        return {
            "document_id": None,
            "document_type": "unknown",
            "processing_status": "failed",
            "status": "failed",
            "nodes_created": 0,
            "interaction_alerts": [],
            "care_gap_alerts": [],
            "confirmation_needed": [],
            "processing_time_ms": 0,
            "error_message": "Document processing services are being configured. Please try again later.",
        }
    except Exception:
        logger.exception(
            "Unexpected error while processing document upload patient_id=%s filename=%s",
            patient_id,
            file.filename,
        )
        return {
            "document_id": None,
            "document_type": "unknown",
            "processing_status": "failed",
            "status": "failed",
            "nodes_created": 0,
            "interaction_alerts": [],
            "care_gap_alerts": [],
            "confirmation_needed": [],
            "processing_time_ms": 0,
            "error_message": "Unexpected error while processing document. Please try again.",
        }

    nodes_count = len(result.nodes_created) if isinstance(result.nodes_created, list) else result.nodes_created

    normalized_result_document_id = _normalize_uuid(result.document_id if result.document_id else None)
    document_id = normalized_result_document_id or str(uuid4())
    doc_record = {
        "document_id": document_id,
        "file_name": file.filename or f"upload.{ext}",
        "document_type": result.document_type or "unknown",
        "valid": False,
        "review_status": "pending_confirmation",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "doctor_name": (result.extracted_data or {}).get("doctor_name") or "",
        "summary": (result.extracted_data or {}).get("summary") or (result.error_message or "Document parsed."),
        "file_url": f"/api/documents/file/{document_id}",
        "extracted_markers": (result.extracted_data or {}).get("labs", []),
        "extracted_data": {
            "doctor_name": (result.extracted_data or {}).get("doctor_name") or "",
            "medications": (result.extracted_data or {}).get("medications", []),
            "labs": (result.extracted_data or {}).get("labs", []),
            "lab_rejections": (result.extracted_data or {}).get("lab_rejections", []),
            "missing_fields": (result.extracted_data or {}).get("missing_fields", []),
            "low_confidence_fields": (result.extracted_data or {}).get("low_confidence_fields", []),
        },
    }
    try:
        add_patient_document(patient_id, doc_record)
        save_pending_document_review(
            patient_id,
            document_id,
            {
                "doctor_name": (result.extracted_data or {}).get("doctor_name") or "",
                "medications": (result.extracted_data or {}).get("medications", []),
                "labs": (result.extracted_data or {}).get("labs", []),
                "lab_rejections": (result.extracted_data or {}).get("lab_rejections", []),
                "missing_fields": (result.extracted_data or {}).get("missing_fields", []),
                "low_confidence_fields": (result.extracted_data or {}).get("low_confidence_fields", []),
                "document_type": result.document_type or "unknown",
            },
        )
    except Exception:
        logger.exception(
            "Failed to persist document metadata/review payload patient_id=%s document_id=%s",
            patient_id,
            document_id,
        )

    await _persist_document_to_db(
        patient_id=patient_id,
        document_id=document_id,
        document_type=result.document_type or "prescription",
        file_url=doc_record["file_url"],
        original_filename=doc_record["file_name"],
        content_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(contents),
        processing_status=result.processing_status or "failed",
        structured_data=doc_record["extracted_data"],
        ocr_text=(result.extracted_data or {}).get("summary") or "",
        ocr_confidence=0.0,
        error_message=result.error_message,
        processing_time_ms=result.processing_time_ms,
    )

    persisted_labs = 0
    lab_persistence = "not_applicable"
    lab_rejections = list((result.extracted_data or {}).get("lab_rejections", []))
    if (result.document_type or "") == "lab_report":
        labs_for_persistence = (result.extracted_data or {}).get("labs", [])
        persisted_labs_ok, persisted_labs, persistence_rejections = await _persist_labs_to_phig_db(
            patient_id=patient_id,
            document_id=document_id,
            labs=labs_for_persistence,
            clinical_entities=(result.extracted_data or {}).get("clinical_entities", []),
        )
        lab_rejections.extend(persistence_rejections)
        lab_persistence = "database" if persisted_labs_ok else "failed"

    notif_title = "Document Processed"
    notif_message = f"{doc_record['file_name']} processed as {doc_record['document_type']}"
    if result.processing_status == "failed":
        notif_title = "Document Processing Failed"
        notif_message = result.error_message or f"Could not extract data from {doc_record['file_name']}."
    elif result.processing_status == "needs_confirmation":
        notif_title = "Document Needs Confirmation"
        notif_message = (
            (result.extracted_data or {}).get("summary")
            or f"Please review extracted details from {doc_record['file_name']}."
        )

    try:
        push_notification(
            patient_id,
            "document",
            notif_title,
            notif_message,
            path="/documents",
            metadata={"document_id": document_id, "status": result.processing_status},
        )

        if result.interaction_alerts:
            push_notification(
                patient_id,
                "interaction",
                "New Interaction Alert",
                f"{len(result.interaction_alerts)} potential interaction(s) detected from latest upload.",
                path="/medications",
                metadata={"document_id": document_id},
            )
    except Exception:
        logger.exception(
            "Failed to create notifications for uploaded document patient_id=%s document_id=%s",
            patient_id,
            document_id,
        )

    return {
        "document_id": document_id,
        "file_name": doc_record["file_name"],
        "document_type": result.document_type,
        "processing_status": result.processing_status,
        "status": result.processing_status,
        "nodes_created": nodes_count,
        "interaction_alerts": result.interaction_alerts or [],
        "care_gap_alerts": result.care_gap_alerts or [],
        "confirmation_needed": result.confirmation_needed or [],
        "processing_time_ms": result.processing_time_ms,
        "error_message": result.error_message,
        "summary": doc_record["summary"],
        "file_url": doc_record["file_url"],
        "extracted_review": doc_record["extracted_data"],
        "labs_added": persisted_labs,
        "lab_persistence": lab_persistence,
        "lab_rejections": lab_rejections,
    }


@router.post("/confirm/{document_id}")
async def confirm_document_extraction(document_id: str, body: ConfirmExtractionRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id, "edit")

    pending = get_pending_document_review(patient_id, document_id)
    if not pending:
        raise HTTPException(status_code=404, detail="No pending extraction review found for this document")

    doctor_name = (body.doctor_name or "").strip() or (pending.get("doctor_name") or "").strip()
    reviewed_meds = []
    for med in body.medications or []:
        reviewed_meds.append(
            {
                "name": (med.name or "").strip(),
                "dosage": (med.dosage or "").strip(),
                "frequency": (med.frequency or "").strip(),
                "dose_to_take": (med.dose_to_take or med.dosage or "").strip(),
            }
        )

    if not reviewed_meds:
        for med in pending.get("medications", []):
            reviewed_meds.append(
                {
                    "name": (med.get("name") or "").strip(),
                    "dosage": (med.get("dosage") or "").strip(),
                    "frequency": (med.get("frequency") or "").strip(),
                    "dose_to_take": (med.get("dose_to_take") or med.get("dosage") or "").strip(),
                }
            )

    missing_fields: list[str] = []
    if not doctor_name:
        missing_fields.append("doctor_name")
    if not reviewed_meds:
        missing_fields.append("medications")
    for i, med in enumerate(reviewed_meds):
        if not med.get("name"):
            missing_fields.append(f"medications[{i}].name")
        if not med.get("dosage"):
            missing_fields.append(f"medications[{i}].dosage")

    if missing_fields:
        return {
            "status": "needs_manual_input",
            "document_id": document_id,
            "missing_fields": missing_fields,
            "low_confidence_fields": pending.get("low_confidence_fields", []),
        }

    phig_meds, pipeline_trace, pipeline_warnings = await _post_confirmation_pipeline(
        patient_id=patient_id,
        doctor_name=doctor_name,
        reviewed_meds=reviewed_meds,
    )

    snapshot_id = await phig_integrity.create_snapshot(
        patient_id=patient_id,
        reason=f"confirm_document:{document_id}",
    )
    pipeline_trace["snapshot"] = "created"

    persisted_to_db, persisted_count = await _persist_medications_to_phig_db(
        patient_id=patient_id,
        document_id=document_id,
        medications=phig_meds,
    )
    if persisted_to_db and persisted_count > 0:
        pipeline_trace["phig_write"] = "ok"
    else:
        add_extracted_medications(patient_id, phig_meds)
        pipeline_trace["phig_write"] = "fallback"

    consistency = await phig_integrity.verify_consistency(patient_id)
    if not consistency.get("passed"):
        rollback_ok = await phig_integrity.rollback_snapshot(patient_id=patient_id, snapshot_id=snapshot_id)
        pipeline_trace["consistency_check"] = "failed"
        pipeline_trace["rollback"] = "applied" if rollback_ok else "failed"
        raise HTTPException(
            status_code=500,
            detail={
                "error": "phig_consistency_failed_after_write",
                "consistency_errors": consistency.get("errors", []),
                "rollback": pipeline_trace["rollback"],
                "pipeline_trace": pipeline_trace,
            },
        )
    pipeline_trace["consistency_check"] = "ok"

    await _persist_document_to_db(
        patient_id=patient_id,
        document_id=document_id,
        document_type=pending.get("document_type") or "prescription",
        file_url=f"/api/documents/file/{document_id}",
        original_filename=f"document_{document_id}.pdf",
        content_type="application/pdf",
        file_size_bytes=0,
        processing_status="success",
        structured_data={
            "doctor_name": doctor_name,
            "medications": phig_meds,
            "pipeline_trace": pipeline_trace,
            "pipeline_warnings": pipeline_warnings,
        },
        ocr_text="",
        ocr_confidence=0.0,
        error_message=None,
        processing_time_ms=None,
    )
    update_patient_document(
        patient_id,
        document_id,
        {
            "valid": True,
            "review_status": "confirmed",
            "doctor_name": doctor_name,
            "summary": f"Confirmed extraction with {len(phig_meds)} medication(s).",
            "extracted_data": {
                "doctor_name": doctor_name,
                "medications": reviewed_meds,
                "missing_fields": [],
                "low_confidence_fields": [],
                "pipeline_trace": pipeline_trace,
                "pipeline_warnings": pipeline_warnings,
            },
        },
    )
    remove_pending_document_review(patient_id, document_id)

    push_notification(
        patient_id,
        "document",
        "Document Confirmed",
        f"{len(phig_meds)} medication(s) confirmed and added to PHIG.",
        path="/medications",
        metadata={"document_id": document_id},
    )

    return {
        "status": "confirmed",
        "document_id": document_id,
        "doctor_name": doctor_name,
        "medications_added": persisted_count if persisted_to_db else len(phig_meds),
        "medications": phig_meds,
        "pipeline_trace": pipeline_trace,
        "pipeline_warnings": pipeline_warnings,
        "persistence": "database" if persisted_to_db else "runtime_fallback",
    }


@router.get("/list")
async def list_documents(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    return {"documents": get_patient_documents(patient_id)}


@router.get("/prescriptions/valid")
async def list_valid_prescriptions(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    if patient_id == DEMO_USER_ID:
        docs = [d for d in get_patient_documents(patient_id) if d.get("document_type") == "prescription" and d.get("valid")]
        return {"documents": docs}
    return {"documents": []}


@router.get("/lab-reports/valid")
async def list_valid_lab_reports(request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    return {"documents": get_valid_lab_reports(patient_id)}


@router.get("/file/{document_id}")
async def get_document_file(document_id: str, request: Request):
    current_user = await auth_mod.get_current_user(request)
    patient_id = request.query_params.get("patient_id", current_user["id"])
    await rbac_mod.verify_patient_access(current_user["id"], patient_id)

    doc = next((d for d in get_patient_documents(patient_id) if d.get("document_id") == document_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    pdf_bytes = generate_uploaded_document_pdf(doc)
    filename = doc.get("file_name") or f"document_{document_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
