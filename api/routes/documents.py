from fastapi import APIRouter, UploadFile, File, Request, HTTPException

import api.middleware.auth as auth_mod
import api.middleware.rbac as rbac_mod
from pipeline.document_pipeline import document_pipeline

router = APIRouter(prefix="/api/documents", tags=["documents"])

ALLOWED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/heic"]
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

    nodes_count = len(result.nodes_created) if isinstance(result.nodes_created, list) else result.nodes_created

    return {
        "document_id": result.document_id,
        "document_type": result.document_type,
        "processing_status": result.processing_status,
        "status": result.processing_status,
        "nodes_created": nodes_count,
        "interaction_alerts": result.interaction_alerts,
        "care_gap_alerts": result.care_gap_alerts,
        "confirmation_needed": result.confirmation_needed,
        "processing_time_ms": result.processing_time_ms,
        "error_message": result.error_message,
    }
