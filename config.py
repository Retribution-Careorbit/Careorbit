import os


class Settings:
    JWT_SECRET: str = os.environ.get("JWT_SECRET", "careorbit-dev-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRY_DAYS: int = 30
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./careorbit.db")
    ENCRYPTION_KEY: str = os.environ.get("ENCRYPTION_KEY", "careorbit-encryption-key-32chars!")
    RATE_LIMIT_MAX_FAILURES: int = 5
    RATE_LIMIT_COOLDOWN_SECONDS: int = 900


_settings = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
