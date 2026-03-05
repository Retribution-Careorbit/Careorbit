from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import Optional

import api.middleware.auth as auth_mod
from agents.orchestrator import orchestrator

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"


@router.post("/query")
async def chat_query(body: ChatRequest, request: Request):
    current_user = await auth_mod.get_current_user(request)

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
