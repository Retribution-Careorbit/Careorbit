import os
from fastapi import APIRouter
from db.session import check_db_connection, check_core_security_schema
from config import get_settings
from services.azure_openai import AzureOpenAIService
from services.azure_search import AzureSearchService
from services.azure_translator import AzureTranslatorService

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    environment = os.environ.get("ENVIRONMENT", "development")
    db_status = await check_db_connection()
    security_schema = await check_core_security_schema()

    return {
        "status": "healthy",
        "service": "careorbit-api",
        "version": "0.3.0",
        "environment": environment,
        "database": db_status,
        "security_schema": security_schema,
    }


@router.get("/health/dependencies")
async def health_dependencies():
    settings = get_settings()

    openai = AzureOpenAIService()
    search = AzureSearchService()
    translator = AzureTranslatorService()

    openai_configured = bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_KEY)
    search_configured = bool(settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_KEY and settings.AZURE_SEARCH_INDEX)
    translator_configured = bool(settings.AZURE_TRANSLATOR_ENDPOINT and settings.AZURE_TRANSLATOR_KEY)

    openai_client_ready = bool(openai._get_client()) if openai_configured else False
    search_client_ready = bool(search._get_client()) if search_configured else False

    dependencies = {
        "azure_openai": {
            "configured": openai_configured,
            "client_ready": openai_client_ready,
            "required_for_chat": settings.CHAT_REQUIRE_OPENAI,
        },
        "azure_search": {
            "configured": search_configured,
            "client_ready": search_client_ready,
            "required_for_chat": settings.CHAT_REQUIRE_SEARCH,
        },
        "azure_translator": {
            "configured": translator_configured,
            "client_ready": translator_configured,
            "required_for_non_en": settings.CHAT_REQUIRE_TRANSLATOR_FOR_NON_EN,
        },
    }

    strict_required = []
    if settings.CHAT_REQUIRE_OPENAI:
        strict_required.append("azure_openai")
    if settings.CHAT_REQUIRE_SEARCH:
        strict_required.append("azure_search")

    missing_required = [
        name for name in strict_required
        if not dependencies[name]["configured"] or not dependencies[name]["client_ready"]
    ]

    status = "ready" if not missing_required else "degraded"

    return {
        "status": status,
        "strict_mode": settings.CHAT_STRICT_AZURE_DEPENDENCIES,
        "missing_required": missing_required,
        "dependencies": dependencies,
    }
