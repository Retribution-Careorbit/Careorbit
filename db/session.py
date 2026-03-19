import os
import asyncio
import logging
from contextlib import asynccontextmanager
from collections import defaultdict
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

logger = logging.getLogger("careorbit.db.session")

_engine = None
_async_session_factory = None
_core_schema_initialized = False
_core_schema_lock = asyncio.Lock()


def _is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql")


def _sanitize_asyncpg_url(db_url: str) -> str:
    """Remove query params unsupported by asyncpg (e.g., sslmode/SSLMODE)."""
    parts = urlsplit(db_url)
    query_items = parse_qsl(parts.query, keep_blank_values=True)
    filtered_items = [(k, v) for (k, v) in query_items if k.strip().lower() != "sslmode"]
    if len(filtered_items) != len(query_items):
        logger.info("Removed sslmode from DATABASE_URL query parameters for asyncpg compatibility")
    new_query = urlencode(filtered_items)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))


def _get_async_engine():
    global _engine
    if _engine is not None:
        return _engine

    from config import get_settings
    settings = get_settings()
    db_url = _sanitize_asyncpg_url(settings.DATABASE_URL)

    if not _is_postgres_url(db_url):
        return None

    try:
        from sqlalchemy.ext.asyncio import create_async_engine

        connect_args = {}
        if ".postgres.database.azure.com" in db_url:
            connect_args["ssl"] = "require"

        _engine = create_async_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        logger.info(f"Async PostgreSQL engine created")
        return _engine
    except Exception as e:
        logger.warning(f"Failed to create async engine: {e}")
        return None


def _get_session_factory():
    global _async_session_factory
    if _async_session_factory is not None:
        return _async_session_factory

    engine = _get_async_engine()
    if engine is None:
        return None

    try:
        from sqlalchemy.ext.asyncio import async_sessionmaker
        _async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
        return _async_session_factory
    except Exception as e:
        logger.warning(f"Failed to create session factory: {e}")
        return None


class AsyncPgSession:
    def __init__(self, sa_session):
        self._session = sa_session

    async def execute(self, query, params=None):
        from sqlalchemy import text
        stmt = text(query) if isinstance(query, str) else query
        if params:
            result = await self._session.execute(stmt, params)
        else:
            result = await self._session.execute(stmt)
        return result

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()

    async def close(self):
        await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._session.close()


class InMemorySession:
    def __init__(self, store):
        self._store = store
        self._execute_history = []

    async def execute(self, query, params=None):
        self._execute_history.append((str(query), params))
        query_str = str(query).lower()

        if "select" in query_str:
            for table_name, rows in self._store.items():
                if table_name in query_str:
                    if params:
                        filtered = [
                            row for row in rows
                            if all(row.get(k) == v for k, v in params.items() if k in row)
                        ]
                        return InMemoryResult(filtered)
                    return InMemoryResult(rows)
            return InMemoryResult([])

        if "insert" in query_str:
            for table_name in self._store:
                if table_name in query_str:
                    if params and isinstance(params, dict):
                        self._store[table_name].append(params)
                    break
            else:
                for word in query_str.split():
                    if word not in ("insert", "into", "values", "(", ")", ",", "select"):
                        if not word.startswith(":") and not word.startswith("'"):
                            self._store[word] = self._store.get(word, [])
                            if params and isinstance(params, dict):
                                self._store[word].append(params)
                            break

        return InMemoryResult([])

    async def commit(self):
        pass

    async def rollback(self):
        pass

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class InMemoryResult:
    def __init__(self, data=None):
        self._data = data or []

    def mappings(self):
        return InMemoryMappings(self._data)

    def first(self):
        return self._data[0] if self._data else None

    def scalar(self):
        if self._data and isinstance(self._data[0], (int, float, str)):
            return self._data[0]
        return len(self._data) if self._data else 0

    def all(self):
        return self._data


class InMemoryMappings:
    def __init__(self, data):
        self._data = data

    def first(self):
        return self._data[0] if self._data else None

    def all(self):
        return self._data


_global_store = defaultdict(list)


def async_session():
    factory = _get_session_factory()
    if factory is not None:
        sa_session = factory()
        return AsyncPgSession(sa_session)

    from config import get_settings
    settings = get_settings()
    strict_production_data_mode = str(os.environ.get("STRICT_PRODUCTION_DATA_MODE", "true")).strip().lower() in {"1", "true", "yes", "on"}
    if settings.ENVIRONMENT == "production" and strict_production_data_mode:
        raise RuntimeError("Database unavailable and in-memory fallback is disabled in production")

    return InMemorySession(_global_store)


def get_engine():
    return _get_async_engine()


async def check_db_connection() -> str:
    from config import get_settings
    settings = get_settings()
    db_url = settings.DATABASE_URL

    if not _is_postgres_url(db_url):
        if "sqlite" in db_url:
            return "sqlite"
        return "in_memory"

    try:
        engine = _get_async_engine()
        if engine is None:
            return "not_configured"
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        return "connected"
    except Exception as e:
        logger.error(f"DB connection check failed: {e}")
        return "error"


async def ensure_core_security_schema() -> None:
    global _core_schema_initialized

    if _core_schema_initialized:
        return

    async with _core_schema_lock:
        if _core_schema_initialized:
            return

        engine = _get_async_engine()
        if engine is None:
            return

        from sqlalchemy import text

        try:
            async with engine.begin() as conn:
                # Keep schema permissive for current runtime IDs/IP formats.
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS refresh_tokens (
                        id TEXT PRIMARY KEY DEFAULT md5(random()::text || clock_timestamp()::text),
                        user_id TEXT NOT NULL,
                        token_hash TEXT NOT NULL UNIQUE,
                        issued_at TIMESTAMPTZ DEFAULT NOW(),
                        expires_at TIMESTAMPTZ NOT NULL,
                        revoked_at TIMESTAMPTZ,
                        ip_address TEXT,
                        user_agent TEXT,
                        replaced_by TEXT
                    )
                """))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash)"))

                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id TEXT PRIMARY KEY DEFAULT md5(random()::text || clock_timestamp()::text),
                        user_id TEXT NOT NULL,
                        patient_id TEXT,
                        action TEXT NOT NULL,
                        ip_address TEXT,
                        user_agent TEXT,
                        metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_log_patient ON audit_log(patient_id)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)"))
                await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at)"))

            _core_schema_initialized = True
        except Exception as exc:
            logger.warning(f"Failed to ensure core security schema: {exc}")
