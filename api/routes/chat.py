import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

import api.middleware.auth as auth_mod
from agents.orchestrator import orchestrator
from db.seed_demo import DEMO_USER_ID, RAMESH_CARE_GAPS
from graph.phig_builder import phig_builder

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger("careorbit.routes.chat")


class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"


async def _build_local_fallback_response(patient_id: str, message: str, language: str, agents_used: list) -> dict:
    query = (message or "").strip().lower()
    meds_payload = await phig_builder.get_medication_subgraph(patient_id)
    medications = meds_payload.get("medications", []) if isinstance(meds_payload, dict) else []

    med_lines = []
    interactions = []
    for med in medications:
        dose = med.get("dosage") or ""
        freq = med.get("frequency") or ""
        med_lines.append(f"{med.get('name', 'Unknown')} ({dose}, {freq})")
        for ix in med.get("interactions", []) or []:
            if isinstance(ix, dict):
                interactions.append(ix)

    if any(k in query for k in ["medication", "medicine", "drug", "tablet", "pill", "prescription"]):
        if med_lines:
            response_message = "Current medications from your profile: " + "; ".join(med_lines) + "."
        else:
            response_message = "No medications are currently recorded in your profile."
    elif any(k in query for k in ["screening", "care gap", "checkup", "preventive", "immunization", "vaccination"]):
        if patient_id == DEMO_USER_ID:
            gap_names = [g.get("name") for g in RAMESH_CARE_GAPS if isinstance(g, dict) and g.get("name")]
            response_message = (
                "Recommended care gaps from your profile: " + ", ".join(gap_names) + "."
                if gap_names else
                "No active care gaps found in your profile."
            )
        else:
            response_message = "I could not find care-gap records for your profile yet."
    elif any(k in query for k in ["interaction", "interactions"]):
        if interactions:
            pairs = []
            for ix in interactions:
                pair = ix.get("drug_pair")
                severity = ix.get("severity")
                if pair:
                    pairs.append(f"{pair} ({severity or 'unknown severity'})")
            response_message = "Potential interaction alerts: " + "; ".join(dict.fromkeys(pairs)) + "."
        else:
            response_message = "No interaction alerts are currently available for your profile."
    else:
        if med_lines:
            response_message = (
                "AI services are temporarily unavailable, but your profile data is available. "
                f"You currently have {len(medications)} medication(s) recorded. "
                "Ask me about medications, interactions, or screenings."
            )
        else:
            response_message = (
                "AI services are temporarily unavailable, and no medication records are available in your profile yet."
            )

    return {
        "message": response_message,
        "language": language,
        "agents_used": agents_used,
        "alerts": interactions,
        "care_gaps": RAMESH_CARE_GAPS if patient_id == DEMO_USER_ID else [],
        "recommendations": [],
        "confidence": 0.55,
    }


@router.post("/query")
async def chat_query(body: ChatRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)

    try:
        result = await orchestrator.process_query(
            patient_id=current_user["id"],
            message=body.message,
            language=body.language or "en",
        )

        return {
            "message": result.message,
            "language": result.language,
            "agents_used": result.agents_used,
            "alerts": result.alerts,
            "care_gaps": result.care_gaps,
            "recommendations": getattr(result, "recommendations", []),
            "confidence": result.confidence,
        }
    except Exception as exc:
        logger.warning(f"Chat orchestrator fallback for user {current_user['id']}: {exc}")
        agents_used = orchestrator._route_to_agents(body.message)
        return await _build_local_fallback_response(
            patient_id=current_user["id"],
            message=body.message,
            language=body.language or "en",
            agents_used=agents_used,
        )
