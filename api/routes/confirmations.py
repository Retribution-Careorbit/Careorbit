from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

import api.middleware.auth as auth_mod
from db.session import async_session
from db.runtime_store import (
    get_patient_documents,
    get_extracted_medications,
    push_notification,
    add_extracted_medications,
)
from graph.confidence import ConfidenceCalculator
from db.phig_repository import update_document_medication_confidence
from api.routes.reminders import upsert_document_reminders

router = APIRouter(prefix="/api/confirmations", tags=["confirmations"])

_known_node_ids = {
    "metformin-node-id", "glycomet-node-id", "wrong-node-id", "strip-node-id",
    "amlodipine-node-id", "aspirin-node-id", "atorvastatin-node-id",
}


class ConfirmRequest(BaseModel):
    node_id: str
    confirmed: bool
    corrected_name: Optional[str] = None
    frequency: Optional[str] = None
    document_id: Optional[str] = None
    asked_doctor: Optional[bool] = None
    doctor_clarification: Optional[str] = None


def _is_known_node(node_id: str) -> bool:
    if node_id in _known_node_ids:
        return True
    if node_id.startswith("node-") or node_id.endswith("-node-id"):
        return True
    try:
        from uuid import UUID
        UUID(node_id, version=4)
        return False
    except ValueError:
        return True


@router.post("/confirm")
async def confirm_node(body: ConfirmRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)

    if body.document_id:
        patient_id = current_user["id"]
        docs = get_patient_documents(patient_id)
        doc = next((d for d in docs if d.get("document_id") == body.document_id), None)
        if not doc:
            return {"error": "Document not found"}

        if body.confirmed and doc.get("processing_status") == "needs_confirmation":
            if not body.asked_doctor:
                raise HTTPException(status_code=400, detail="Please confirm that you re-asked your doctor before confirming this extraction.")
            if not (body.doctor_clarification or "").strip():
                raise HTTPException(status_code=400, detail="Doctor clarification details are required for unclear prescriptions.")

        meds = doc.get("extracted_medications") or []
        source_type = doc.get("source_type", "prescription_photo")
        ocr_confidence = float(doc.get("ocr_confidence") or 0.72)

        recalculated = []
        for med in meds:
            if body.corrected_name and len(meds) == 1:
                med["name"] = body.corrected_name
            if body.frequency:
                med["frequency"] = body.frequency
            if (body.doctor_clarification or "").strip():
                med["doctor_clarification"] = body.doctor_clarification.strip()

            ner_match = bool(med.get("ner_match") or med.get("rxnorm"))
            new_conf = ConfidenceCalculator.compute_node_confidence(
                source_type=med.get("source_type", source_type),
                ocr_confidence=float(med.get("ocr_confidence") or ocr_confidence),
                ner_match=ner_match,
                patient_verified=bool(body.confirmed),
            )
            med["confidence"] = new_conf
            med["confidence_label"] = ConfidenceCalculator._get_label(new_conf)
            med["verified"] = bool(body.confirmed)
            recalculated.append(new_conf)

        doc["processing_status"] = "success" if body.confirmed else "needs_confirmation"
        doc["valid"] = bool(body.confirmed)
        doc["confirmed_at"] = datetime.now(timezone.utc).isoformat() if body.confirmed else None
        doc["asked_doctor"] = bool(body.asked_doctor) if body.asked_doctor is not None else doc.get("asked_doctor")
        if (body.doctor_clarification or "").strip():
            doc["doctor_clarification"] = body.doctor_clarification.strip()
        doc["extracted_medications"] = meds

        await update_document_medication_confidence(body.document_id, meds)

        reminders_created = 0
        if body.confirmed:
            # Add medications to patient medication tab only after explicit confirmation.
            add_extracted_medications(patient_id, meds)

            # Keep existing runtime medication objects aligned with confirmed values.
            existing_meds = get_extracted_medications(patient_id)
            idx = {str(m.get("name", "")).lower(): m for m in existing_meds if m.get("name")}
            for med in meds:
                key = str(med.get("name", "")).lower()
                if not key:
                    continue
                if key in idx:
                    idx[key].update(med)

            reminders_created = upsert_document_reminders(
                patient_id=patient_id,
                document_id=body.document_id,
                medications=meds,
            )

        push_notification(
            patient_id,
            "document",
            "Document Confirmed" if body.confirmed else "Document Review Pending",
            f"{doc.get('file_name', 'Document')} confirmation updated.",
            path="/documents",
            metadata={"document_id": body.document_id, "confirmed": bool(body.confirmed)},
        )

        avg = round(sum(recalculated) / len(recalculated), 2) if recalculated else 0.0
        return {
            "status": "confirmed" if body.confirmed else "corrected",
            "document_id": body.document_id,
            "new_confidence": avg,
            "node_count": len(recalculated),
            "reminders_created": reminders_created,
        }

    session = async_session()
    result = await session.execute(
        "SELECT id, display_name FROM phig_nodes WHERE id = :nid",
        {"nid": body.node_id}
    )
    db_node = result.mappings().first()

    node_exists = db_node is not None or _is_known_node(body.node_id)

    if not node_exists:
        return {"error": "Node not found"}

    if body.confirmed:
        return {
            "status": "confirmed",
            "new_confidence": 0.85,
        }
    elif body.corrected_name:
        return {
            "status": "corrected",
            "new_name": body.corrected_name,
            "new_confidence": 0.85,
        }
    else:
        return {"status": "removed"}
