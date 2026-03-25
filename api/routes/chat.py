import logging
from uuid import uuid4

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional

import api.middleware.auth as auth_mod
from agents.orchestrator import orchestrator, AzureDependencyUnavailable

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger("careorbit.routes.chat")


class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "en"


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
            "translation_used": getattr(result, "response_metadata", {}).get("translation_used", False),
            "source_language": getattr(result, "response_metadata", {}).get("source_language", body.language or "en"),
            "safety_interventions_applied": getattr(result, "response_metadata", {}).get("safety_interventions_applied", []),
            "confidence_warning": getattr(result, "response_metadata", {}).get("confidence_warning"),
            "degraded_mode": False,
        }
    except AzureDependencyUnavailable as exc:
        trace_id = str(uuid4())
        logger.error(f"Chat dependency failure trace_id={trace_id} user={current_user['id']} failures={exc.failures}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "azure_dependencies_unavailable",
                "message": "Required Azure AI dependencies are currently unavailable for chat processing.",
                "trace_id": trace_id,
                "dependencies": exc.failures,
                "degraded_mode": False,
            },
        )
    except Exception as exc:
        logger.warning(f"Chat orchestrator error for user {current_user['id']}: {exc}")
        result = await orchestrator.build_grounded_response(
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
            "translation_used": getattr(result, "response_metadata", {}).get("translation_used", False),
            "source_language": getattr(result, "response_metadata", {}).get("source_language", body.language or "en"),
            "safety_interventions_applied": getattr(result, "response_metadata", {}).get("safety_interventions_applied", []),
            "confidence_warning": getattr(result, "response_metadata", {}).get("confidence_warning"),
            "degraded_mode": True,
        }
