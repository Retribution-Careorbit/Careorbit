from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import StreamingResponse
import io
import logging
from datetime import datetime, timezone
from uuid import uuid4

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from db.seed_demo import DEMO_USER_ID, RAMESH_UPLOADED_DOCUMENTS
from pipeline.document_pipeline import document_pipeline
from utils.pdf_generator import generate_uploaded_document_pdf
from db.runtime_store import (
    get_patient_documents,
    add_patient_document,
    get_valid_lab_reports,
    add_extracted_medications,
    push_notification,
)

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = logging.getLogger("careorbit.routes.documents")

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic", "application/pdf"]
MAX_SIZE = 10 * 1024 * 1024


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

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed. Allowed: {ALLOWED_TYPES}")

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

    document_id = result.document_id or f"doc-{uuid4().hex[:8]}"
    doc_record = {
        "document_id": document_id,
        "file_name": file.filename or f"upload.{ext}",
        "document_type": result.document_type or "unknown",
        "valid": result.processing_status in {"success", "needs_confirmation"},
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "doctor_name": "Uploaded Document",
        "summary": (result.extracted_data or {}).get("summary") or (result.error_message or "Document parsed."),
        "file_url": f"/api/documents/file/{document_id}",
        "extracted_markers": (result.extracted_data or {}).get("labs", []),
    }
    try:
        add_patient_document(patient_id, doc_record)

        extracted_meds = (result.extracted_data or {}).get("medications", [])
        if extracted_meds:
            add_extracted_medications(patient_id, extracted_meds)
    except Exception:
        logger.exception(
            "Failed to persist document metadata/medications patient_id=%s document_id=%s",
            patient_id,
            document_id,
        )

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
