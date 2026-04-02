import os
import logging

logger = logging.getLogger("careorbit.config")

_KEYVAULT_SECRET_MAP = {
    "DATABASE-URL": "DATABASE_URL",
    "AZURE-OPENAI-ENDPOINT": "AZURE_OPENAI_ENDPOINT",
    "AZURE-OPENAI-KEY": "AZURE_OPENAI_KEY",
    "AZURE-DI-ENDPOINT": "AZURE_DI_ENDPOINT",
    "AZURE-DI-KEY": "AZURE_DI_KEY",
    "AZURE-LANGUAGE-ENDPOINT": "AZURE_LANGUAGE_ENDPOINT",
    "AZURE-LANGUAGE-KEY": "AZURE_LANGUAGE_KEY",
    "AZURE-SEARCH-ENDPOINT": "AZURE_SEARCH_ENDPOINT",
    "AZURE-SEARCH-KEY": "AZURE_SEARCH_KEY",
    "AZURE-SEARCH-INDEX": "AZURE_SEARCH_INDEX",
    "AZURE-TRANSLATOR-ENDPOINT": "AZURE_TRANSLATOR_ENDPOINT",
    "AZURE-TRANSLATOR-KEY": "AZURE_TRANSLATOR_KEY",
    "AZURE-COMM-CONNECTION-STRING": "AZURE_COMM_CONNECTION_STRING",
    "AZURE-BLOB-CONNECTION-STRING": "AZURE_BLOB_CONNECTION_STRING",
    "APPINSIGHTS-CONNECTION-STRING": "APPINSIGHTS_CONNECTION_STRING",
    "JWT-SECRET-KEY": "JWT_SECRET_KEY",
    "PG-ENCRYPTION-KEY": "PG_ENCRYPTION_KEY",
}


def _load_keyvault_secrets() -> dict:
    uri = os.environ.get("AZURE_KEYVAULT_URI")
    if not uri:
        return {}

    try:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=uri, credential=credential)
        secrets = {}
        for kv_name, env_name in _KEYVAULT_SECRET_MAP.items():
            try:
                secret = client.get_secret(kv_name)
                secrets[env_name] = secret.value
                logger.info(f"Loaded secret {kv_name} from Key Vault")
            except Exception as e:
                logger.debug(f"Secret {kv_name} not found in Key Vault: {e}")
        return secrets
    except ImportError:
        logger.warning("azure-identity/azure-keyvault-secrets not installed, skipping Key Vault")
        return {}
    except Exception as e:
        logger.warning(f"Key Vault connection failed, falling back to env vars: {e}")
        return {}


class Settings:
    def __init__(self):
        kv_secrets = _load_keyvault_secrets()

        def _get(key: str, default: str = "") -> str:
            return kv_secrets.get(key) or os.environ.get(key, default)

        self.JWT_SECRET: str = _get("JWT_SECRET_KEY") or _get("JWT_SECRET", "careorbit-dev-secret-key-change-in-production")
        self.JWT_ALGORITHM: str = "HS256"
        self.JWT_EXPIRY_MINUTES: int = int(_get("JWT_EXPIRY_MINUTES", "15") or "15")
        self.REFRESH_TOKEN_EXPIRY_DAYS: int = int(_get("REFRESH_TOKEN_EXPIRY_DAYS", "30") or "30")
        self.DATABASE_URL: str = _get("DATABASE_URL", "sqlite+aiosqlite:///./careorbit.db")
        self.ENCRYPTION_KEY: str = _get("PG_ENCRYPTION_KEY") or _get("ENCRYPTION_KEY", "careorbit-encryption-key-32chars!")
        self.RATE_LIMIT_MAX_FAILURES: int = 5
        self.RATE_LIMIT_COOLDOWN_SECONDS: int = 900
        self.ENVIRONMENT: str = _get("ENVIRONMENT", "development")

        self.AZURE_OPENAI_ENDPOINT: str = _get("AZURE_OPENAI_ENDPOINT", "")
        self.AZURE_OPENAI_KEY: str = _get("AZURE_OPENAI_KEY", "")
        self.AZURE_DI_ENDPOINT: str = _get("AZURE_DI_ENDPOINT", "")
        self.AZURE_DI_KEY: str = _get("AZURE_DI_KEY", "")
        self.AZURE_LANGUAGE_ENDPOINT: str = _get("AZURE_LANGUAGE_ENDPOINT", "")
        self.AZURE_LANGUAGE_KEY: str = _get("AZURE_LANGUAGE_KEY", "")
        self.AZURE_SEARCH_ENDPOINT: str = _get("AZURE_SEARCH_ENDPOINT", "")
        self.AZURE_SEARCH_KEY: str = _get("AZURE_SEARCH_KEY", "")
        self.AZURE_SEARCH_INDEX: str = _get("AZURE_SEARCH_INDEX", "careorbit-medical-index")
        self.AZURE_TRANSLATOR_ENDPOINT: str = _get("AZURE_TRANSLATOR_ENDPOINT", "")
        self.AZURE_TRANSLATOR_KEY: str = _get("AZURE_TRANSLATOR_KEY", "")
        self.AZURE_COMM_CONNECTION_STRING: str = _get("AZURE_COMM_CONNECTION_STRING", "")
        self.AZURE_BLOB_CONNECTION_STRING: str = _get("AZURE_BLOB_CONNECTION_STRING", "")
        self.APPINSIGHTS_CONNECTION_STRING: str = _get("APPINSIGHTS_CONNECTION_STRING", "")

        def _to_bool(value: str, default: bool) -> bool:
            if value is None or value == "":
                return default
            return str(value).strip().lower() in {"1", "true", "yes", "on"}

        self.ENTRA_ENABLED: bool = _to_bool(_get("ENTRA_ENABLED", "false"), False)
        self.ENTRA_CLIENT_ID: str = _get("ENTRA_CLIENT_ID", "")
        self.ENTRA_CLIENT_SECRET: str = _get("ENTRA_CLIENT_SECRET", "")
        self.ENTRA_TENANT_ID: str = _get("ENTRA_TENANT_ID", "")
        self.ENTRA_OPENID_CONFIG_URL: str = _get("ENTRA_OPENID_CONFIG_URL", "")
        self.ENTRA_REDIRECT_URI: str = _get("ENTRA_REDIRECT_URI", "")
        self.ENTRA_FRONTEND_CALLBACK_URL: str = _get("ENTRA_FRONTEND_CALLBACK_URL", "http://localhost:5000/auth/callback")
        self.ENTRA_SCOPES: str = _get("ENTRA_SCOPES", "openid profile email offline_access")
        self.ENTRA_GOOGLE_DOMAIN_HINT: str = _get("ENTRA_GOOGLE_DOMAIN_HINT", "")
        self.ENTRA_APPLE_DOMAIN_HINT: str = _get("ENTRA_APPLE_DOMAIN_HINT", "")

        self.DOCUMENTS_ALLOW_PDF_UPLOADS: bool = _to_bool(_get("DOCUMENTS_ALLOW_PDF_UPLOADS", "false"), False)
        self.DOCUMENTS_REQUIRE_BLOB_DURABILITY: bool = _to_bool(
            _get("DOCUMENTS_REQUIRE_BLOB_DURABILITY", "true"),
            True,
        )

        # Strict chat mode: fail fast with explicit errors if required Azure dependencies fail.
        self.CHAT_STRICT_AZURE_DEPENDENCIES: bool = _to_bool(_get("CHAT_STRICT_AZURE_DEPENDENCIES", "true"), True)
        self.CHAT_REQUIRE_OPENAI: bool = _to_bool(_get("CHAT_REQUIRE_OPENAI", "true"), True)
        self.CHAT_REQUIRE_SEARCH: bool = _to_bool(_get("CHAT_REQUIRE_SEARCH", "true"), True)
        self.CHAT_REQUIRE_TRANSLATOR_FOR_NON_EN: bool = _to_bool(_get("CHAT_REQUIRE_TRANSLATOR_FOR_NON_EN", "false"), False)
        self.CHAT_ENABLE_TRANSLATION_DISCLAIMER: bool = _to_bool(_get("CHAT_ENABLE_TRANSLATION_DISCLAIMER", "true"), True)
        self.CHAT_ENABLE_ROUNDTRIP_VALIDATION: bool = _to_bool(_get("CHAT_ENABLE_ROUNDTRIP_VALIDATION", "true"), True)
        self.CHAT_HIGH_RISK_ESCALATION_REQUIRED: bool = _to_bool(_get("CHAT_HIGH_RISK_ESCALATION_REQUIRED", "true"), True)
        self.CHAT_TRANSLATION_TIMEOUT_MS: int = int(_get("CHAT_TRANSLATION_TIMEOUT_MS", "8000") or "8000")
        self.CHAT_TRANSLATION_RETRIES: int = int(_get("CHAT_TRANSLATION_RETRIES", "2") or "2")
        self.CHAT_ROUNDTRIP_DRIFT_THRESHOLD: float = float(_get("CHAT_ROUNDTRIP_DRIFT_THRESHOLD", "0.40") or "0.40")


_settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
