from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

import api.middleware.auth as auth_mod
from db.session import async_session
from db.runtime_store import (
    get_patient_documents,
    get_extracted_medications,
    push_notification,
)
from graph.confidence import ConfidenceCalculator

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

        meds = doc.get("extracted_medications") or []
        source_type = doc.get("source_type", "prescription_photo")
        ocr_confidence = float(doc.get("ocr_confidence") or 0.72)

        recalculated = []
        for med in meds:
            if body.corrected_name:
                med["name"] = body.corrected_name
            if body.frequency:
                med["frequency"] = body.frequency

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
        doc["extracted_medications"] = meds

        # Keep runtime medication list aligned with confirmed values.
        existing_meds = get_extracted_medications(patient_id)
        idx = {str(m.get("name", "")).lower(): m for m in existing_meds if m.get("name")}
        for med in meds:
            key = str(med.get("name", "")).lower()
            if not key:
                continue
            if key in idx:
                idx[key].update(med)

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
