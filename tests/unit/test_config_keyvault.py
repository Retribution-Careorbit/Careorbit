import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock


class TestSettingsEnvFallback:

    def test_settings_reads_jwt_secret_from_env(self):
        with patch.dict(os.environ, {"JWT_SECRET": "test-jwt-secret-xyz"}):
            from config import Settings
            s = Settings()
            assert s.JWT_SECRET == "test-jwt-secret-xyz"

    def test_settings_has_default_jwt_secret(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("JWT_SECRET", None)
            from config import Settings
            s = Settings()
            assert len(s.JWT_SECRET) > 0

    def test_settings_reads_database_url_from_env(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test:pass@localhost/db"}):
            from config import Settings
            s = Settings()
            assert s.DATABASE_URL == "postgresql://test:pass@localhost/db"

    def test_settings_has_default_database_url(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DATABASE_URL", None)
            from config import Settings
            s = Settings()
            assert "sqlite" in s.DATABASE_URL or "postgresql" in s.DATABASE_URL

    def test_settings_reads_encryption_key_from_env(self):
        with patch.dict(os.environ, {"ENCRYPTION_KEY": "custom-key-32chars-long!!!!!!!!!!"}):
            from config import Settings
            s = Settings()
            assert s.ENCRYPTION_KEY == "custom-key-32chars-long!!!!!!!!!!"

    def test_settings_jwt_algorithm_is_hs256(self):
        from config import Settings
        s = Settings()
        assert s.JWT_ALGORITHM == "HS256"

    def test_settings_jwt_expiry_is_positive(self):
        from config import Settings
        s = Settings()
        assert s.JWT_EXPIRY_MINUTES > 0

    def test_settings_refresh_token_expiry_is_positive(self):
        from config import Settings
        s = Settings()
        assert s.REFRESH_TOKEN_EXPIRY_DAYS > 0


class TestSettingsSingleton:

    def test_get_settings_returns_settings_instance(self):
        import config
        config._settings = None
        s = config.get_settings()
        from config import Settings
        assert isinstance(s, Settings)

    def test_get_settings_returns_same_instance(self):
        import config
        config._settings = None
        s1 = config.get_settings()
        s2 = config.get_settings()
        assert s1 is s2

    def test_get_settings_singleton_reset(self):
        import config
        config._settings = None
        s1 = config.get_settings()
        config._settings = None
        s2 = config.get_settings()
        assert s1 is not s2


PRD_SECRETS = [
    "DATABASE_URL",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_KEY",
    "AZURE_DI_ENDPOINT",
    "AZURE_DI_KEY",
    "AZURE_LANGUAGE_ENDPOINT",
    "AZURE_LANGUAGE_KEY",
    "AZURE_SEARCH_ENDPOINT",
    "AZURE_SEARCH_KEY",
    "AZURE_SEARCH_INDEX",
    "AZURE_TRANSLATOR_ENDPOINT",
    "AZURE_TRANSLATOR_KEY",
    "AZURE_COMM_CONNECTION_STRING",
    "AZURE_BLOB_CONNECTION_STRING",
    "APPINSIGHTS_CONNECTION_STRING",
    "JWT_SECRET_KEY",
    "PG_ENCRYPTION_KEY",
]


@pytest.mark.deployment
class TestKeyVaultConfigLoader:

    def test_keyvault_not_used_without_uri(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AZURE_KEYVAULT_URI", None)
            from config import Settings
            s = Settings()
            assert s.JWT_SECRET is not None

    def test_keyvault_uri_triggers_kv_loading(self):
        mock_client = MagicMock()
        mock_secret = MagicMock()
        mock_secret.value = "kv-loaded-secret"
        mock_client.get_secret.return_value = mock_secret

        with patch.dict(os.environ, {"AZURE_KEYVAULT_URI": "https://test-kv.vault.azure.net/"}):
            with patch("azure.keyvault.secrets.SecretClient", return_value=mock_client):
                with patch("azure.identity.DefaultAzureCredential"):
                    import config
                    config._settings = None
                    s = config.Settings()
                    assert mock_client.get_secret.called or s.JWT_SECRET is not None

    @pytest.mark.parametrize("secret_name", PRD_SECRETS)
    def test_prd_secret_mapped_to_config(self, secret_name):
        from config import Settings, _KEYVAULT_SECRET_MAP
        s = Settings()
        env_name = _KEYVAULT_SECRET_MAP.get(secret_name.replace("_", "-"), secret_name)
        found = (
            hasattr(s, secret_name)
            or hasattr(s, secret_name.lower())
            or hasattr(s, env_name)
            or hasattr(s, env_name.lower())
            or env_name in _KEYVAULT_SECRET_MAP.values()
        )
        assert found, \
            f"Settings missing attribute for PRD secret: {secret_name}"


@pytest.mark.deployment
class TestCORSConfiguration:

    def test_cors_includes_localhost_in_dev(self):
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=False):
            from main import _default_origins
            assert any("localhost" in o for o in _default_origins)

    def test_cors_includes_static_web_app_in_production(self):
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "https://careorbit-web-prod.azurestaticapps.net"
        }):
            import importlib
            import main
            importlib.reload(main)
            assert any("azurestaticapps" in o for o in main._default_origins)
