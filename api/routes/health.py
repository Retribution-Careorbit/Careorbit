import os
from fastapi import APIRouter
from db.session import check_db_connection
from config import get_settings
from services.azure_openai import AzureOpenAIService
from services.azure_search import AzureSearchService
from services.azure_translator import AzureTranslatorService

router = APIRouter(tags=["health"])


def _entra_health(settings):
    required = {
        "ENTRA_CLIENT_ID": bool(settings.ENTRA_CLIENT_ID),
        "ENTRA_CLIENT_SECRET": bool(settings.ENTRA_CLIENT_SECRET),
        "ENTRA_REDIRECT_URI": bool(settings.ENTRA_REDIRECT_URI),
        "ENTRA_FRONTEND_CALLBACK_URL": bool(settings.ENTRA_FRONTEND_CALLBACK_URL),
        "ENTRA_SCOPES": bool(settings.ENTRA_SCOPES),
    }
    authority_present = bool(settings.ENTRA_OPENID_CONFIG_URL or settings.ENTRA_TENANT_ID)
    required["ENTRA_AUTHORITY"] = authority_present

    missing_required = [key for key, configured in required.items() if not configured]
    enabled = bool(settings.ENTRA_ENABLED)
    ready = enabled and not missing_required

    return {
        "enabled": enabled,
        "ready": ready,
        "missing_required": missing_required,
        "configured": {
            "ENTRA_CLIENT_ID": required["ENTRA_CLIENT_ID"],
            "ENTRA_CLIENT_SECRET": required["ENTRA_CLIENT_SECRET"],
            "ENTRA_REDIRECT_URI": required["ENTRA_REDIRECT_URI"],
            "ENTRA_FRONTEND_CALLBACK_URL": required["ENTRA_FRONTEND_CALLBACK_URL"],
            "ENTRA_SCOPES": required["ENTRA_SCOPES"],
            "ENTRA_AUTHORITY": required["ENTRA_AUTHORITY"],
        },
    }


@router.get("/health")
async def health_check():
    environment = os.environ.get("ENVIRONMENT", "development")
    db_status = await check_db_connection()

    return {
        "status": "healthy",
        "service": "careorbit-api",
        "version": "0.3.0",
        "environment": environment,
        "database": db_status,
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
        "entra": _entra_health(settings),
        "dependencies": dependencies,
    }


@router.get("/health/auth")
async def health_auth():
    settings = get_settings()
    entra = _entra_health(settings)
    return {
        "status": "ready" if entra["ready"] else "degraded",
        "provider": "azure-entra-id",
        "entra": entra,
    }


@router.get("/health/startup")
async def health_startup():
    settings = get_settings()
    db_status = await check_db_connection()
    entra = _entra_health(settings)

    checks = {
        "database": {
            "ready": db_status in ("connected", "sqlite", "in_memory", "not_configured"),
            "status": db_status,
        },
        "entra_auth": {
            "ready": entra["ready"],
            "enabled": entra["enabled"],
            "missing_required": entra["missing_required"],
        },
    }

    overall_ready = checks["database"]["ready"] and (not entra["enabled"] or checks["entra_auth"]["ready"])

    return {
        "status": "ready" if overall_ready else "degraded",
        "checks": checks,
    }
